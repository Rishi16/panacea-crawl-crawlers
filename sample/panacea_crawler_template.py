import os

import general
from panacea_crawl import Spider

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
                "category_path",
                "category_url",
                "product_url_mod",
                "product_url",
                "page_url",
                "deal_type",
            ]
        )

    # Crawler begins here.
    # input_row list will contain a single tab separated input from the input_file
    def initiate(self, input_row, region, proxies_from_tool, thread_name):
        data, session = general.get_url("https://www.google.com")
        cache_page_url = general.save_cache(data["text"])
        self.push_data("found", [[cache_page_url]])


if __name__ == "__main__":
    crawl = Crawler(current_path)
    crawl.start(crawl.initiate)
