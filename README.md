# ************* WebsiteExplorer
![Logo](app.ico)

A simple script for browsing the ************* website and extract the products data.

It is written in python and a .exe binary is generated for Windows users.

## Installing dependencies
All mandatory libraries and dependancies are listed in `requirements.txt`.
```bash
pip install -r ./requirements.txt
```

## Generating a new binary
Do not forget to change the script version in `products_explorer.py` file line 18: `SCRIPT_VERSION=X.X`.

Run the following command to build the .exe binary:
```bash
python setup.py build
```
The generated binary is located to `./dist/product_explorer.exe`

## Command-line help
```
usage: python products_explorer.py [-h] [-b FIRST_PAGE] [-e LAST_PAGE] base_url

Browse the ************ website to extract the products data.

positional arguments:
  base_url              The website URL

optional arguments:
  -h, --help            show this help message and exit
  -b FIRST_PAGE, --begin FIRST_PAGE
                        First page to begin browsing
  -e LAST_PAGE, --end LAST_PAGE
                        Last page to end browsing
```

## Other commands
* `python setup.py clean` : for cleaning temp and generated files
* `python setup.py lint` : for linting the script file
* `python setup.py fmt` : for formatting the script file
