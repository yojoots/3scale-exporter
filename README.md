# Exporting 3scale CMS data

## Overview

This is a bespoke export script to scrape the data out of an existing site that was built or managed through the 3scale CMS. This was originally built to help with version control and source management of 3scale website data through a parallel GitHub repository. Though there have been discussions and rumblings about RedHat/3scale providing a real, official API to do this sort of thing, at the time of writing no such API is available.

**DISCLAIMER**: this is not an official tool of any kind, and if 3scale changes their UI or API, functionality might be impacted. With that said, because this solely handles exportation and doesn't make or save any changes to the CMS content, there is hopefully not much potential for harm.


## Setup:
```
pip install -r requirements.txt
```

On Linux, the pyperclip module makes use of xclip (or xsel). You may need to install it:

```
sudo apt-get install xclip
```

To export the 3scale data, pass the export.py file your admin username and password like so:

```
python export.py -b https://YOUR-LOGIN-URL.3scale.net -u USERNAME -p PASSWORD
```

By default, it will export **everything** in the CMS. You can use the `-s` option to skip certain sections/files, or use `--help` for more options.

## Miscellaneous notes

- Some partials include `/` in their names, but in general filenames can't contain this character. The export script replaces `/` with `-` in partial names.
- The "meta" folder contains internal data or settings of the pages/files in 3scale. Every file is a .html file so that these can be easily viewed in a browser.
- Both draft and live versions of each page are saved (with the draft version being saved as `filename(draft).ext`)
- If the `--all` flag is true (which by default is the case), then Partials and Layouts data will still export, even if their respective flags are false. Remember to set `--all` to False if you'd like to skip the export of either (or both) of these.