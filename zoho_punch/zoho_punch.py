import json
import os
import pickle
import re
import time
from datetime import datetime
from selenium.webdriver.common.by import By
import panacea_crawl.general as general
from panacea_crawl.panacea_crawl import Spider
import requests
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
        self.zoho_session = None

    # Crawler begins here.
    # input_row list will contain a single tab separated input from the input_file
    def initiate(self, input_row, region, proxies_from_tool, thread_name):
        if os.path.exists('zoho_session'):
            self.zoho_session = pickle.load(open('zoho_session', 'rb'))
        if os.path.exists('zoho_punch_status'):
            status = pickle.load(open('zoho_punch_status', 'rb'))
            time_passed = datetime.now() - status
            if time_passed.seconds > 9*60*60 and time_passed.days == 0:
                self.punch("punchOut")
                os.remove('zoho_punch_status')
            else:
                print(f"Punch Out Failed! {'Time Exceeded' if time_passed.days != 0 else 'Hours not complete'}: {status.strftime('%m/%d/%Y, %H:%M:%S')}")
        else:
            self.punch("punchIn")

    def punch(self, type):
        relogin = True
        print(self.zoho_session)
        if self.zoho_session:
            url = f"https://people.zoho.com/hrmsbct/AttendanceAction.zp?mode={type}"
            payload = {
                'conreqcsr': str(self.zoho_session["CSRF"]),
                'urlMode': 'home_dashboard',
                'latitude': '18.5195521',
                'longitude': '73.9456645',
                'accuracy': '21.613'}
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Cookie': self.zoho_session['Cookie'],
                'Origin': 'https://people.zoho.com',
                'Referer': 'https://people.zoho.com/hrmsbct/zp',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                              'like Gecko) Chrome/107.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            try:
                response = requests.request("POST", url, headers=headers, data=payload).json()
                if not response.get('msg', {}).get('error', '') and not response.get('code') == 'INVALID_CSRF_TOKEN':
                    relogin = False
                pickle.dump(datetime.now(), open('zoho_punch_status', 'wb'))
                print(response)
            except json.JSONDecoder as e:
                print(e)
                pass
        if relogin:
            data, driver = general. get_url2(url='https://people.zoho.com/hrmsbct/zp#home/dashboard', tag_to_find='//a[@class="zgh-login"]', close_session=False, all_requests=True, images=True)
            if general.wait_driver(driver, '//a[@class="zgh-login"]', 10):
                general.click(driver, '//a[@class="zgh-login"]')
                general.wait_driver(driver, '//button[@id="nextbtn" and @class="btn blue"]', 60)
                general.send_text(driver, "rishikesh.shendkar@blueconchtech.com",
                                  '//input[@id="login_id" and @name="LOGIN_ID"]', 0, click=True)
            if general.wait_driver(driver, '//div[@class="ZPPimg dropdown"]', 10):
                pass
            elif general.wait_driver(driver, '//div[@id="lightbox"]', 30):
                general.send_text(driver, "rishikesh.shendkar@blueconchtech.com", '//input[@type="email"]', 0, click=True)
                general.wait_driver(driver, '//input[@name="passwd"]', 30)
                time.sleep(5)
                general.send_text(driver, "678yui^&*", '//input[@name="passwd"]', 0, click=True)
                approved = general.wait_driver(driver, '//div[@id="KmsiDescription" and contains(text(),"Do this to reduce the number")]', 120)
                if approved:
                    general.click(driver, '//input[@type="submit"]')
                else:
                    print("Please approve the Authenticator request on your phone.")
            if general.wait_driver(driver, '//div[@class="ZPPimg dropdown"]', 120):
                if general.find_elements_driver(driver, '//div[@id="ZPD_Top_Att_Stat" and @class="in CP"]'):
                    print("Currently Checked Out")
                    if type == "punnchIn":
                        print("Checking In")
                        general.click(driver, '//div[@id="ZPD_Top_Att_Stat" and @class="in CP"]')
                        general.wait_driver(driver, '//div[@id="ZPD_Top_Att_Stat" and @class="out CP"]', 60)
                        pickle.dump(datetime.now(), open('zoho_punch_status', 'wb'))
                elif general.find_elements_driver(driver, '//div[@id="ZPD_Top_Att_Stat" and @class="out CP"]'):
                    print("Currently Checked In")
                    # in_time =
                    if type == "punchOut":
                        print("Checking Out")
                        general.click(driver, '//div[@id="ZPD_Top_Att_Stat" and @class="out CP"]')
                        general.wait_driver(driver, '//div[@id="ZPD_Top_Att_Stat" and @class="in CP"]', 60)

                for request in driver.requests:
                    if 'https://people.zoho.com/hrmsbct/viewPhoto' in request.url:
                        headers = dict(request.headers)
                        csrf = re.findall(r'(?<=CSRF_TOKEN=)[^;]*(?=;)', headers["Cookie"])[0]
                        pickle.dump({"CSRF": csrf, "Cookie": headers["Cookie"]}, open('zoho_session', 'wb'))
                        break


if __name__ == "__main__":
    crawl = Crawler(current_path)
    crawl.start(crawl.initiate)

    # crawl.punch("punchIn")
