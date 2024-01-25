from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime
import os
from random import randint
import sys
import time
import traceback
import unicodedata

from bs4 import BeautifulSoup
from openpyxl import Workbook
import requests

# Script version
SCRIPT_VERSION = 1.01
SCRIPT_NAME = "MaxtonExplorer"
SCRIPT_FULLNAME = f"{SCRIPT_NAME} {SCRIPT_VERSION}"


class ExcelExporter:
    """Helper class for writing excel file."""

    def __init__(self, filename):
        self.filename = filename
        self.row = 1
        self.workbook = Workbook()
        self.worksheet = self.workbook.active

    def write_file(self):
        self.workbook.save(self.filename)

    def add_line(self, items: list):
        for index, item in enumerate(items):
            self.worksheet.cell(row=self.row, column=index + 1, value=item)
        self.row = self.row + 1
        self.write_file()


# Script vars
website_name = "maxton-design"
product_count = 0
# Export file
now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
exporter = ExcelExporter(f"products_{now}.xlsx")


def browse_page(page_url, page_number):
    """Browse all products pages and extract each product data."""

    global product_count

    log(f"Parsing page {page_number}: {page_url}")
    # Parse the page
    page_request = requests.get(page_url)
    data = BeautifulSoup(page_request.content, "html.parser")

    # Get all products links
    products = data.find_all("a", class_="product-name")
    log(f"Find {len(products)} products")

    # For each product
    for product in products:
        try:
            parse_product(product["href"])
            product_count += 1
        except Exception as e:
            log("Cannot parse product", e)
            exporter.add_line([f"Error parsing product: {e}"])


def parse_product(product_url):
    """Parse the product page and extract its data."""

    log(f"  -> [{product_count}] Parsing product: {product_url}")

    # Parse the product page
    product_request = requests.get(product_url)
    product_data = BeautifulSoup(product_request.content, "html.parser")

    # Extract data
    product = {}
    product["ref"] = product_data.find("div", class_="proj_code").find("strong").text
    product["title"] = product_data.find("div", class_="projector_navigation").find("h1").text
    # Extract category from <title>
    category = product_data.find("title").text
    category_selector = "Notre Offre \\ "
    category_sub = category.rfind(category_selector)
    product["category"] = category[(category_sub + len(category_selector)) : -len(f" | {website_name}")].replace(
        " \\ ", ">"
    )
    # Extract images links
    product["images"] = []
    for img in product_data.find("div", class_="photos").find_all("a", class_="projector_medium_image"):
        product["images"].append(f"{base_url}{img['href']}")
    # Extract description
    description = str(product_data.find(id="component_projector_longdescription")).replace("\n", "<br>")
    product["description"] = description.replace("\n", "<br>")
    # Extract price
    price = product_data.find(id="projector_price_value").text
    price = unicodedata.normalize("NFKD", price)
    price = float(price.replace("€", "").replace(",", ".").replace(" ", ""))
    price = str(price).replace(".", ",")

    # Extract variant names and prices
    variants = []
    variants_data = product_data.find("div", class_="fancy-select")
    if variants_data:
        variants_data = variants_data.find_all("li")
        if len(variants_data) > 0:
            for variant in variants_data:
                if "selected" in variant["class"]:
                    variants.append(
                        {
                            "price": price,
                            "finition": variant["data-title"],
                            "subref": product["ref"],
                        }
                    )
                else:
                    product_id = variant["data-product"]
                    variant_id = variant["data-values_id"]
                    response = requests.get(
                        f"""{base_url}/ajax/projector.php?product={product_id}&
                        size=uniw&get=sizes,sizeprices&multiversions[selected]=
                        {variant_id}&multiversions[last_selected]={variant_id}"""
                    )
                    res = response.json()
                    variant_price = float(res["sizeprices"]["value"])
                    variant_price = str(variant_price).replace(".", ",")
                    variants.append(
                        {
                            "price": variant_price,
                            "finition": variant["data-title"],
                            "subref": res["sizes"]["code"],
                        }
                    )
    elif product_data.find("div", class_="product_section versions") and product_data.find(
        "div", class_="product_section versions"
    ).find(
        "div", class_="product_section_sub"
    ):  # Old products, different way to parse
        variants_data = (
            product_data.find("div", class_="product_section versions")
            .find("div", class_="product_section_sub")
            .find_all("a")
        )
        if len(variants_data) > 0:
            for variant in variants_data:
                if "active" in variant["class"]:
                    variants.append(
                        {
                            "price": price,
                            "finition": variant.find("div", class_="version_name").text,
                            "subref": product["ref"],
                        }
                    )
                else:
                    response = requests.get(base_url + variant["href"])
                    res = BeautifulSoup(response.content, "html.parser")
                    variant_price = product_data.find(id="projector_price_value").text
                    variant_price = unicodedata.normalize("NFKD", price)
                    variant_price = float(price.replace("€", "").replace(",", ".").replace(" ", ""))
                    variant_price = str(price).replace(".", ",")
                    variants.append(
                        {
                            "price": variant_price,
                            "finition": variant["title"],
                            "subref": res.find("div", class_="proj_code").find("strong").text,
                        }
                    )

    if not variants:
        variants.append(
            {
                "price": price,
                "finition": "",
                "subref": product["ref"],
            }
        )

    # Write in the output file, one line per variant
    for v in variants:
        product["subref"] = v["subref"]
        product["price"] = v["price"]
        product["finition"] = v["finition"]
        try:
            export_product(product)
        except Exception as e:
            log("Cannot export product", e)
            exporter.add_line([f"Error writing product: {e}"])

    # Randomize delay for preventing request spam
    random_delay()


def export_product(product):
    """Exporting the product data."""

    log(f"    * Exporting product: {product['title']} - {product['finition']}")

    exporter.add_line(
        [
            product["ref"],
            product["subref"],
            product["title"],
            product["price"],
            product["finition"],
            product["category"],
            ", ".join(product["images"]),
            product["description"],
        ]
    )


def log(message, exception=None):
    print(message)
    if exception:
        traceback.print_exception(exception)


def random_delay():
    """Random sleep between 0.5 and 2sec."""
    time.sleep(float(randint(5, 20)) / 10)


def check_value(value):
    """Validate argument value."""
    ivalue = int(value)
    if ivalue < 0 or ivalue > 56:
        raise ArgumentTypeError(f"Invalid value {value}")
    return ivalue


if __name__ == "__main__":
    parser = ArgumentParser(
        prog=f"python {os.path.basename(__file__).replace('.py', '.exe')}",
        description=f"{SCRIPT_FULLNAME} - Browse the {website_name} website to extract the products data.",
    )
    parser.add_argument("-v", "--version", action="version", version=SCRIPT_FULLNAME)
    parser.add_argument(
        "-b",
        "--begin",
        dest="first_page",
        type=check_value,
        default=0,
        required=False,
        help="First page to begin browsing",
    )
    parser.add_argument(
        "-e",
        "--end",
        dest="last_page",
        type=check_value,
        default=100,
        required=False,
        help="Last page to end browsing",
    )
    parser.add_argument(
        "-p",
        "--product",
        dest="product_url",
        required=False,
        help="Specific product URL to export",
    )
    args = parser.parse_args()
    if args.first_page > args.last_page:
        raise ArgumentTypeError(f"Invalid arguments: {args.first_page} > {args.last_page}")

    base_url = "https://maxton.design"
    products_url = f"{base_url}/fre_m_Notre-Offre-1876.html"

    # Parse a specific product
    if args.product_url:
        parse_product(args.product_url)

    else:
        # For each catalog page
        for page_number in range(args.first_page, args.last_page):
            page_url = f"{products_url}?counter={page_number}"
            browse_page(page_url, page_number)

    input("\nExecution completed. Press 'Enter' to exit...")
    sys.exit(0)
