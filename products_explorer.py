import argparse
from datetime import datetime
import os
from random import randint
import time
import traceback
import unicodedata

from bs4 import BeautifulSoup
from openpyxl import Workbook
import requests

anonymous_name = "*************"

# TODO voir description dernière balise vide qui fout la merde ?
# TODO 500 produits par fichier excel
# TODO useragent
# TODO indicateur de progression


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


def browse_page(page_url, page_number):
    """Browse all products pages and extract each product data."""

    log(f"Parsing page {page_number}: {page_url}")
    # Parse the page
    page_request = requests.get(page_url)
    data = BeautifulSoup(page_request.content, "html.parser")

    # Get all products links
    products = data.find_all("a", class_="product_wrapper_hover")
    log(f"Find {len(products)} products")

    # Generate filename for this page
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_filename = f"products_{now}_{page_number}.xlsx"
    exporter = ExcelExporter(export_filename)

    # For each product
    for product in products:
        try:
            parse_product(product["href"], exporter)
        except Exception as e:
            log("Cannot parse product", e)


def parse_product(product_url, exporter: ExcelExporter):
    """Parse the product page and extract its data."""

    log(f"  -> Parsing product: {product_url}")
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
    product["category"] = category[(category_sub + len(category_selector)) : -len(f" | {anonymous_name}")].replace(
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
        else:
            # TODO fix code duplication
            variants.append(
                {
                    "price": price,
                    "finition": "",
                    "subref": product["ref"],
                }
            )
    else:
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
            export_product(product, exporter)
        except Exception as e:
            log("Cannot export product", e)

    # Randomize delay for preventing request spam
    random_delay()


def export_product(product, exporter: ExcelExporter):
    """Exporting the product data."""

    log(f"    -> Exporting product: {product['title']} - {product['finition']}")

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
        raise argparse.ArgumentTypeError(f"Invalid value {value}")
    return ivalue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog=f"python {os.path.basename(__file__)}",
        description=f"Browse the {anonymous_name} website to extract the products data.",
    )
    parser.add_argument(
        dest="base_url",
        type=str,
        help="The website URL",
    )
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
        default=56,
        required=False,
        help="Last page to end browsing",
    )
    args = parser.parse_args()
    if args.first_page > args.last_page:
        raise argparse.ArgumentTypeError(f"Invalid arguments: {args.first_page} > {args.last_page}")

    base_url = args.base_url.rstrip("/")
    products_url = f"{base_url}/fre_m_Notre-Offre-1876.html"

    # For each catalog page
    for count in range(args.first_page, args.last_page):
        page_url = f"{products_url}?counter={count}"
        browse_page(page_url, count)
