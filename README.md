# Exporting 3scale CMS data

## Overview

This is a bespoke export script to scrape the data out of an existing site that was built or managed through the 3scale CMS. Though there have been discussions and rumblings about making a real, official API available to do this sort of thing, at the time of writing such an API is not available.

**DISCLAIMER**: this is not an official tool of any kind. Because of that, and the fact that the 3scale CMS tool, as well as its underlying API, may change at any moment, without any guarantee of backwards compatibility, I cannot in good faith recommend this tool for production use.


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