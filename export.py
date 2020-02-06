from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import os, pyperclip, platform
from argparse import ArgumentParser

# Function to help our argparser understand boolean strings
def str2bool(v):
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise Exception("Boolean value expected.")


# Command line args setup
parser = ArgumentParser()
parser.add_argument("-b", "--url", dest="url", help="Base URL for 3scale CMS access", metavar="URL")
parser.add_argument("-u", "--user", dest="username", help="Admin username for 3scale CMS access", metavar="USERNAME")
parser.add_argument(
    "-p", "--password", dest="password", help="Admin password for 3scale CMS access", metavar="PASSWORD"
)
parser.add_argument(
    "-v", "--verbose", action="store_true", dest="verbose", default=True, help="Print progress info to stdout"
)
parser.add_argument(
    "-q", "--quiet", action="store_false", dest="verbose", default=False, help="Don't print progress info to stdout"
)
parser.add_argument("-a", "--all", dest="all", type=str2bool, default=True, help="Export all data")
parser.add_argument("--layouts", "--layout", type=str2bool, dest="layouts", default=False, help="Export Layout data")
parser.add_argument(
    "--partials", "--partial", type=str2bool, dest="partials", default=False, help="Export Partials data"
)
parser.add_argument("-g", "--get", dest="get", nargs="+", help="Export single file from CMS", required=False)
parser.add_argument("-s", "--skip", dest="skip", nargs="+", help="Sections you would like to skip", required=False)
args = parser.parse_args()

# We need login information
credentials = True
if not args.url:
    print("Please provide 3scale base login URL with the -b option")
    credentials = False
if not args.username:
    print("Please provide 3scale admin username with the -u option")
    credentials = False
if not args.password:
    print("Please provide 3scale admin password with the -p option")
    credentials = False
if not credentials:
    quit()

# Basic settings
base_url = args.url
start_url = base_url + "/p/admin/cms/templates"
base_path = os.getcwd()

# Create new browser session
driver = webdriver.Firefox()
driver.implicitly_wait(15)
driver.get(start_url)
wait = WebDriverWait(driver, 3)

# Log in
driver.find_element(By.XPATH, '//*[@id="session_username"]').send_keys(args.username)
driver.find_element(By.XPATH, '//*[@id="session_password"]').send_keys(args.password)
driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/main/div[1]/form/div[3]/div/button").click()

# Show all content
try:
    driver.find_element(By.XPATH, '//*[@id="cms-sidebar-filter-origin"]//li[@data-filter-origin="all"]').click()
except:
    print("Expected sidebar content not found. Login may have failed.")
    driver.quit()
    quit()

# Cross-platform support (accommodate Macs)
commandKey = Keys.CONTROL
if platform.system() == "Darwin":
    commandKey = Keys.COMMAND

# Create select-all+copy action chain
select_and_copy = ActionChains(driver)
select_and_copy.key_down(commandKey)
select_and_copy.send_keys("a")
select_and_copy.key_up(commandKey)
select_and_copy.key_down(commandKey)
select_and_copy.send_keys("c")
select_and_copy.key_up(commandKey)

# Write internal 3scale file data (metadata) to "meta" folder
# (.html for convenience)
def write_meta_info(full_path, content_url, item_type):
    driver.get(content_url)
    meta_soup = BeautifulSoup(driver.page_source, "html.parser")
    content = ""
    if item_type == "Section":
        meta_div = meta_soup.find("form", {"id": "edit_cms_section"})
        # Remove noisy token that makes git-diffs much more annoying to compare
        noisyToken = meta_div.find("input", {"name": "authenticity_token"})
        noisyToken.decompose()
        content = meta_div.renderContents()
    elif item_type == "File":
        content = meta_soup.find("form", {"id": "edit_cms_file"}).renderContents()
    else:
        try:
            # Grab the div with all our meta information
            meta_div = meta_soup.find("div", {"id": "cms-template-fields-wrapper"})
            # Un-hide the advanced info
            content = meta_div.renderContents().replace('<ol style="display: none;">', "<ol>")
        except:
            return

    # open, write, and close meta file
    meta_file = open(full_path + ".html", "wb")  # FHSU
    meta_file.write(content)
    meta_file.close()


# Retrieve and save draft and live versions of a Page
def write_actual_content(full_path, content_url, item_type):
    if item_type == "File":
        return

    first_period_index = full_path.find(".")
    if first_period_index < 0:
        file_extension = ".html"
    else:
        file_extension = full_path[first_period_index:]
        full_path = full_path[:first_period_index]

    driver.get(content_url)

    try:
        draft_area = driver.find_element(By.XPATH, '//div[@id="cms-template-draft"]')
        draft_area.click()
        select_and_copy.perform()
        draft_content = pyperclip.paste().encode("utf-8")

        # open, write, and close draft file
        draft_file = open(full_path + "(draft)" + file_extension, "wb")  # FHSU
        draft_file.write(draft_content)
        draft_file.close()
    except:
        print("Error: cms-template-draft not copied (might be empty):" + content_url)

    try:
        published_tab = driver.find_element(By.XPATH, '//a[@href="#cms-template-live"]')
        published_tab.click()
        wait.until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, '//li[@aria-controls="cms-template-live" and @aria-selected="true"]')
            )
        )
        published_area = driver.find_element(By.XPATH, '//div[@id="cms-template-live"]')
        published_area.click()
        select_and_copy.perform()
        published_content = pyperclip.paste().encode("utf-8")

        # open, write, and close live file
        published_file = open(full_path + file_extension, "wb")  # FHSU
        published_file.write(published_content)
        published_file.close()
    except:
        print("Error: cms-template-live not copied (might be empty):" + content_url)

    if args.verbose:
        print(full_path + " : " + content_url)


def recursive_parse_section(relative_path, section_name):
    if args.skip and section_name in args.skip:
        return
    if len(relative_path) > 0:
        next_path = relative_path + "/" + section_name
    else:
        next_path = "/" + section_name
    # Create section-name directory
    if not os.path.exists(base_path + next_path):
        os.makedirs(base_path + next_path)
    if not os.path.exists(base_path + "/meta" + next_path):
        os.makedirs(base_path + "/meta" + next_path)
    # Get section's main URL
    section_url = driver.current_url
    section_soup = BeautifulSoup(driver.page_source, "html.parser")
    write_meta_info(base_path + "/meta" + next_path, section_url, "Section")

    for tr in section_soup.find("table", {"id": "subsections-container"}).find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        first_column = tds[0].find("a")
        next_url = first_column["href"]
        item_name = first_column.contents[0]
        item_type = tds[1].renderContents()
        if item_type == "Section":
            driver.get(base_url + next_url)
            recursive_parse_section(next_path, item_name)
        else:
            write_meta_info(base_path + "/meta" + next_path + "/" + item_name, base_url + next_url, item_type)
            write_actual_content(base_path + next_path + "/" + item_name, base_url + next_url, item_type)
        driver.get(section_url)


def export_all():
    # Root
    sidebar_main_content = driver.find_elements_by_xpath('//div[@id="cms-sidebar-content"]//li//a')
    sidebar_main_content[0].click()
    wait.until(expected_conditions.presence_of_element_located((By.XPATH, '//table[@id="subsections-container"]')))
    if args.all:
        recursive_parse_section("", "Root")

    page_soup = BeautifulSoup(driver.page_source, "html.parser")

    if args.all or args.layouts:
        ### Layouts
        # Create Layouts directories
        if not os.path.exists(base_path + "/Layouts"):
            os.makedirs(base_path + "/Layouts")
        if not os.path.exists(base_path + "/meta/Layouts"):
            os.makedirs(base_path + "/meta/Layouts")

        # Scrape and save Layout content
        for a in page_soup.find("div", {"id": "cms-sidebar-layouts"}).find_all("a"):
            href = a["href"]
            item_name = a["title"]
            write_meta_info(base_path + "/meta/Layouts/" + item_name, base_url + href, "Layout")
            write_actual_content(base_path + "/Layouts/" + item_name, base_url + href, "Layout")

    if args.all or args.partials:
        ### Partials
        # Create Partials directories
        if not os.path.exists(base_path + "/Partials"):
            os.makedirs(base_path + "/Partials")
        if not os.path.exists(base_path + "/meta/Partials"):
            os.makedirs(base_path + "/meta/Partials")

        # Scrape and save Partials content
        for a in page_soup.find("div", {"id": "cms-sidebar-partials"}).find_all("a"):
            href = a["href"]
            item_name = a["title"].replace("/", "-")
            write_meta_info(base_path + "/meta/Partials/" + item_name, base_url + href, "Partial")
            write_actual_content(base_path + "/Partials/" + item_name, base_url + href, "Partial")


if args.get:
    try:
        write_actual_content(args.get[0], args.get[1], "Page")
    except:
        print(
            "Please make sure you're using the --get flag correctly: python export.py -u USERNAME -p PASSWORD -g FULL_PATH PAGE_URL"
        )
else:
    export_all()

# end the Selenium browser session
driver.quit()
