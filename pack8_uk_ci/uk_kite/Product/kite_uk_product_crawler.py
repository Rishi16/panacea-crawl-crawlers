import json
import os
import random
import re
import time

import panacea_crawl.general as general
from panacea_crawl.panacea_crawl import Spider


current_path = os.path.dirname(os.path.abspath(__file__))


class Crawler(Spider):
    def __init__(self, current_path, object=None):
        super().__init__(current_path, object=object)
        if r"panacea\team_data" in current_path.lower():
            super().debug(False)
        else:
            print("Debug: True")
            super().debug(True)
            super().print_requests(True)
        super().cache()
        general.header_values(
            [
                "Category",
                "Category URL",
                "Product Name",
                "Product URL",
                "Part Number",
                "Image",
                "Description",
                "Dimension (mm)",
                "Dimension (inch)",
                "Unit Type",
                "Unit Size",
                "Quantity Range",
                "Price per Quantity",
                "Price Per KG",
                "Price Per Metre",
                "Price Per Unit",
                "Specification"
            ]
        )
        self.websites = {}
        self.base_url = "https://www.kitepackaging.co.uk"

    # Crawler begins here.
    # input_row list will contain a single tab separated input from the input_file
    def initiate(self, input_row, region, proxies_from_tool, thread_name):
        time.sleep(random.randint(3, 7))
        data, session = general.get_url(input_row[3])
        product_data = general.xpath(
            data["source"], '//script[@id="ang-data-source"]/text()'
        )
        product_data = product_data.split("=", 1)
        if len(product_data) != 2:
            self.push_data2("pnf", [input_row])
        json_data = product_data[1].strip().rstrip(";")

        try:
            data = json.loads(json_data)
            if not data.get('productTables'):
                self.push_data2("pnf", [input_row])
            category, category_url, name, url = input_row
            push_products = []
            for products in data.get('productTables'):
                for product in products["products"]:
                    part_number = product.get("partNumber")
                    image = "|".join([img['thumbnailLocation'] for img in product.get("images")])
                    description = product.get("description")
                    specification = " | ".join([f"{spec.get('description')} : {spec.get('value')}" for spec in product.get("specifications")])
                    dim = general.json(product, 'internalDimensions') if general.json(product, 'internalDimensions') else general.json(product, 'externalDimensions')
                    if dim:
                        dimension_mm = f"{general.json(dim, 'length')}x{general.json(dim, 'width')}x{general.json(dim, 'height')}"
                    else:
                        dimension_mm = general.json(product, 'basketDescription')
                    dim = general.json(product, 'basketDescription').split(" ")
                    di = dim[1].replace("(", "").replace(" ", "")
                    dimension_inch = di if len(dim) > 1 and re.match(r'^[xX0-9.]+$', di) else ""
                    pack_size = general.json(product, 'packSize')
                    unit_type = "Pack"
                    for quantity_range, quantity_price, kg_price, metre_price, unit_price in self.quantity_extraction(general.json(product), 'packBreaks'):
                        push_products.append([category, category_url, name, url, part_number, image, description, dimension_mm, dimension_inch, unit_type, pack_size, quantity_range, quantity_price, kg_price, metre_price, unit_price, specification])
                    pallet_size = general.json(product, 'palletSize')
                    unit_type = "Pallet"
                    for quantity_range, quantity_price, kg_price, metre_price, unit_price in self.quantity_extraction(general.json(product), 'palletBreaks'):
                        push_products.append([category, category_url, name, url, part_number, image, description, dimension_mm, dimension_inch, unit_type, pallet_size, quantity_range, quantity_price, kg_price, metre_price, unit_price, specification])
                if push_products:
                    self.push_data2("found", push_products)
                else:
                    self.push_data2("pnf", [input_row])

        except Exception as e:
            self.push_data2("other_exception", [input_row])

    @staticmethod
    def quantity_extraction(data, quantity_key):
        quantity_details = []
        for pack in general.json(data, quantity_key):
            quantity_range = f"{general.json(pack, 'min')}-{general.json(pack, 'max')}"
            quantity_price = general.json(pack, "price")
            kg_price = general.json(pack, 'pricePerKilogram')
            metre_price = general.json(pack, 'pricePerMetre')
            unit_price = general.json(pack, 'pricePerUnit')
            quantity_details.append([quantity_range, quantity_price, kg_price, metre_price, unit_price])
        return quantity_details


if __name__ == "__main__":
    crawl = Crawler(current_path)
    crawl.start(crawl.initiate)
