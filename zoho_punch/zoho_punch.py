import json
import os
import pickle
import re
import time
from datetime import datetime, date
from selenium.webdriver.common.by import By
import panacea_crawl.general as general
from panacea_crawl.panacea_crawl import Spider
import requests
from hidden import secrets
from infi.systray import SysTrayIcon

current_path = os.path.dirname(os.path.abspath(__file__))


class Crawler(Spider):
    def __init__(self, current_path, object=None):
        super().__init__(current_path, object=object)
        print("Debug: True")
        super().debug(True)
        super().print_requests(True)
        self.zoho_session = None
        self.holidays = [(date(2022, 1, 26), date(2022, 3, 8), date(2022, 5, 1), date(2022, 8, 15),
                          date(2022, 9, 19), date(2022, 10, 2), date(2022, 10, 24),
                          date(2022, 11, 13))]

        self.systray = SysTrayIcon("icons/zoho_red.ico", 'Startup')
        self.systray.start()

    # Crawler begins here.
    # input_row list will contain a single tab separated input from the input_file
    def initiate(self, input_row, region, proxies_from_tool, thread_name):
        while True:
            if datetime.now().isoweekday() in range(1, 7) and date.today() not in self.holidays and datetime.now().hour not in range(0, 6):
                self.logger.info("Initiating")
                if os.path.exists('zoho_session'):
                    self.zoho_session = pickle.load(open('zoho_session', 'rb'))
                    self.logger.info(f"Zoho Session: {json.dumps(self.zoho_session)}")
                    # To bored to do it. Quiting half way. I am a quitter
                    # if not os.path.exists('zoho_holidays'):
                    #     try:
                    #         reponse = self.request_zoho(
                    #             "https://people.zoho.com/hrmsbct/listHolidays.zp")
                    #     except Exception as e:
                    #         pass
                if os.path.exists('zoho_punched_in'):
                    in_time = pickle.load(open('zoho_punched_in', 'rb'))
                    self.logger.info(f"In Time: {in_time.strftime('%m/%d/%Y, %H:%M:%S')}")
                    time_passed = datetime.now() - in_time
                    if time_passed.seconds > 9 * 60 * 60 and time_passed.days == 0:
                        self.logger.info(f"Punching Out. 9 Hrs Complete.")
                        self.punch("punchOut", str(time_passed.seconds/3600))
                    else:
                        self.logger.info(
                            f"Punch Out Failed! Hours not complete': "
                            f"{in_time.strftime('%m/%d/%Y, %H:%M:%S')}")
                    self.systray.update('icons/zoho_green.ico', f'Checked In: {in_time.strftime(" %H:%M")}  Hours: {time_passed.seconds//3600}:{int((time_passed.seconds%3600)//60)}')
                elif os.path.exists('zoho_punched_out'):
                    out_time = pickle.load(open('zoho_punched_out', 'rb'))
                    self.logger.info(f"Out Time: {out_time.strftime('%m/%d/%Y, %H:%M:%S')}")
                    if datetime.now().day != out_time.day:
                        self.logger.info(f"New day. Punching In.")
                        self.punch("punchIn")
                else:
                    self.logger.info("New Beginnings")
                    self.punch("punchIn")
            time.sleep(60*15)

    def punch(self, punch_type, punch_in_time=None):
        relogin = True
        if self.zoho_session:
            try:
                url = f"https://people.zoho.com/hrmsbct/AttendanceAction.zp?mode={punch_type}"
                response = self.request_zoho(url).json()
                punch_time = datetime.now()
                if not response.get('msg', {}).get('error', '') and not response.get(
                        'code') == 'INVALID_CSRF_TOKEN':
                    self.logger.info(f"Positive: {response}")
                    relogin = False
                if punch_type == "punchIn":
                    self.logger.info(
                        f"Punch In Successful: {punch_time.strftime('%m/%d/%Y, %H:%M:%S')}")
                    pickle.dump(punch_time, open('zoho_punched_in', 'wb'))
                    os.remove('zoho_punched_out')
                    self.systray.update('icons/zoho_green.ico', f'Checked In: {punch_time.strftime(" %H:%M")}')
                if punch_type == "punchOut":
                    self.logger.info(
                        f"Punch Out Successful: {punch_time.strftime('%m/%d/%Y, %H:%M:%S')}")
                    pickle.dump(punch_time, open('zoho_punched_out', 'wb'))
                    os.remove('zoho_punched_in')
                    self.systray.update('icons/zoho_red.ico', f'Checked Out: {punch_time.strftime(" %H:%M")}  Hours: {punch_in_time.seconds//3600}:{(punch_in_time.seconds%3600)//60}')

            except json.JSONDecoder as e:
                self.logger.info(f"Session Expired.")
                pass
        if relogin:
            self.logger.info(f"Session restore started. Opening Zoho")
            data, driver = general.get_url2(url='https://people.zoho.com/hrmsbct/zp#home/dashboard',
                                            tag_to_find='//a[@class="zgh-login"]',
                                            close_session=False, all_requests=True, images=True)
            if general.wait_driver(driver, '//a[@class="zgh-login"]', 10):
                self.logger.info(f"Logging in")
                general.click(driver, '//a[@class="zgh-login"]')
                general.wait_driver(driver, '//button[@id="nextbtn" and @class="btn blue"]', 60)
                self.logger.info(f"Zoho Email")
                general.send_text(driver, secrets["email"],
                                  '//input[@id="login_id" and @name="LOGIN_ID"]', 0, click=True)
            if general.wait_driver(driver, '//div[@class="ZPPimg dropdown"]', 10):
                pass
            elif general.wait_driver(driver, '//div[@id="lightbox"]', 30):
                self.logger.info(f"Microsoft Login Email")
                general.send_text(driver, secrets["email"], '//input[@type="email"]', 0, click=True)
                general.wait_driver(driver, '//input[@name="passwd"]', 30)
                time.sleep(5)
                self.logger.info(f"Microsoft Login Password")
                general.send_text(driver, secrets["password"], '//input[@name="passwd"]', 0,
                                  click=True)
                approved = general.wait_driver(driver,
                                               '//div[@id="KmsiDescription" and contains(text(),'
                                               '"Do this to reduce the number")]',
                                               120)
                self.logger.info(f"Waiting for Authenticator")
                if approved:
                    self.logger.info(f"Authenticator Approved")
                    general.click(driver, '//input[@type="submit"]')
                else:
                    print("Please approve the Authenticator request on your phone.")
            if general.wait_driver(driver, '//div[@class="ZPPimg dropdown"]', 120):
                self.logger.info(f"On Zoho Dashboard")
                punch_time = datetime.now()
                if general.find_elements_driver(driver,
                                                '//div[@id="ZPD_Top_Att_Stat" and @class="in CP"]'):
                    self.logger.info("Currently Checked Out")
                    if punch_type == "punnchIn":
                        self.logger.info("Checking In")
                        general.click(driver, '//div[@id="ZPD_Top_Att_Stat" and @class="in CP"]')
                        general.wait_driver(driver,
                                            '//div[@id="ZPD_Top_Att_Stat" and @class="out CP"]', 60)
                        pickle.dump(punch_time, open('zoho_punched_in', 'wb'))
                        self.logger.info(
                            f"Punch In Successful: {punch_time.strftime('%m/%d/%Y, %H:%M:%S')}")
                        os.remove('zoho_punched_out')
                        self.systray.update('icons/zoho_green.ico',
                                            f'Checked In: {punch_time.strftime(" %H:%M")}')

                elif general.find_elements_driver(driver,
                                                  '//div[@id="ZPD_Top_Att_Stat" and @class="out '
                                                  'CP"]'):
                    self.logger.info("Currently Checked In")
                    # in_time =
                    if punch_type == "punchOut":
                        self.logger.info("Checking Out")
                        general.click(driver, '//div[@id="ZPD_Top_Att_Stat" and @class="out CP"]')
                        general.wait_driver(driver,
                                            '//div[@id="ZPD_Top_Att_Stat" and @class="in CP"]', 60)
                        pickle.dump(punch_time, open('zoho_punched_out', 'wb'))
                        self.logger.info(
                            f"Punch Out Successful: "
                            f"{punch_time.strftime('%m/%d/%Y, %H:%M:%S')}")
                        os.remove('zoho_punched_in')
                        self.systray.update('icons/zoho_red.ico',
                                            f'Checked Out: {punch_time.strftime(" %H:%M")}  Hours: {punch_in_time.seconds//3600}:{(punch_in_time.seconds%3600)//60}')

                for request in driver.requests:
                    if 'https://people.zoho.com/hrmsbct/viewPhoto' in request.url:
                        headers = dict(request.headers)
                        csrf = re.findall(r'(?<=CSRF_TOKEN=)[^;]*(?=;)', headers["Cookie"])[0]
                        pickle.dump({"CSRF": csrf, "Cookie": headers["Cookie"]},
                                    open('zoho_session', 'wb'))
                        self.logger.info("New session saved.")
                        break

    def request_zoho(self, url):
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
            return requests.request("POST", url, headers=headers, data=payload)
        except Exception as e:
            self.logger.error(f"Request Error: {general.get_error_line(e)}")
            raise e


if __name__ == "__main__":
    crawl = Crawler(current_path)
    crawl.start(crawl.initiate)

    # crawl.punch("punchIn")
