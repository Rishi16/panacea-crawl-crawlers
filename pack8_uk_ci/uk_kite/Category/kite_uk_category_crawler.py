import os

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
            ["Category", "Category URL", "Product Name", "Product URL"]
        )
        self.websites = {}
        self.base_url = "https://www.kitepackaging.co.uk"
        self.pushed_urls = []
        self.traversed_urls = []

    # Crawler begins here.
    # input_row list will contain a single tab separated input from the input_file
    def initiate(self, input_row, region, proxies_from_tool, thread_name):
        data, session = general.get_url(input_row[0])
        self.traversed_urls.append(input_row[0])
        urls = general.xpath(
            data["source"], '//div[@class="dropdown-submenu list-group"]/a', mode="set"
        )
        for url in urls:
            link = self.base_url + general.xpath(url, "@href")
            name = general.clean(url.text_content())
            self.sub_cat_traverse(link, session, input_row, name)

    def sub_cat_traverse(self, link, session, input_row, name):
        if link not in self.traversed_urls:
            cat_page, session = general.get_url(link, session=session)
            sub_cat = general.xpath(cat_page["source"], '//div[@class="product-group-container"]//a[@class="tile-link"]', mode="set")
            self.traversed_urls.append(link)
            if sub_cat:
                for sc in sub_cat:
                    name = general.clean(general.xpath(sc, '*//h4/text()'))
                    sub_url = self.base_url + general.xpath(sc, "@href")
                    self.sub_cat_traverse(sub_url, session, input_row, name)
            else:
                if link not in self.pushed_urls:
                    self.push_data2("found", [[input_row[1], input_row[0], name, link]])
                    self.pushed_urls.append(link)
                else:
                    print(f"Already added {name}")
        else:
            print(f"Already visited {name}")


if __name__ == "__main__":
    crawl = Crawler(current_path)
    crawl.start(crawl.initiate)
