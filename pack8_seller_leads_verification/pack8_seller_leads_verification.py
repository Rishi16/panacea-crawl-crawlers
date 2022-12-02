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
        general.header_values(["Website", "Keyword Macthed"])
        self.websites = {}
        self.keywords = (
            "void fill",
            "void filling",
            "cushion",
            "geami",
            "paper wrap",
            "coil",
            "ecommerce",
            "transit",
            "damage",
            "shredded",
            "hexacel",
            "honeycomb",
        )

    # Crawler begins here.
    # input_row list will contain a single tab separated input from the input_file
    def initiate(self, input_row, region, proxies_from_tool, thread_name):
        data, session = general.get_url(input_row[0], proxies=False)
        self.websites[input_row[0]] = set()
        website = input_row[0].split(".", 1)[1]
        if not self.traverse(data, website, input_row[0]):
            self.push_data2("found", [[input_row[0], "NO"]])
        del self.websites[input_row[0]]
        # cache_page_url = general.save_cache(data["text"])
        # self.push_data("found", [[cache_page_url]])

    def traverse(self, data, website, full_url):
        urls = [
            url
            for url in list(set(general.xpath(data["source"], "//a/@href", mode="set")))
            if website in url and url.startswith("https") and url not in self.websites
        ]
        for url in urls:
            self.websites[full_url].add(url)
            data, session = general.get_url(url, proxies=False)
            if any(keyword in data["text"].lower() for keyword in self.keywords):
                self.push_data2("found", [[full_url, "YES"]])
                return True
            else:
                done = self.traverse(data, website, full_url)
                if done:
                    return True
        return False


if __name__ == "__main__":
    crawl = Crawler(current_path)
    crawl.start(crawl.initiate)
