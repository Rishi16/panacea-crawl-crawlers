import json
import os
import pickle
import random
import re
import sys
import time
from datetime import datetime, date

from PIL import Image
from selenium.webdriver.common.by import By
import panacea_crawl.general as general
from panacea_crawl.panacea_crawl import Spider
import requests
from hidden import secrets
from infi.systray import SysTrayIcon
from win10toast import ToastNotifier

current_path = os.path.dirname(os.path.abspath(__file__))


class Crawler(Spider):
    def __init__(self, current_path, object=None):
        super().__init__(current_path, object=object)
        print("Debug: True")
        super().debug(True)
        super().print_requests(True)
        self.zoho_session = None
        self.red_icon = current_path + "\\icons\\zoho_red.ico"
        self.green_icon = current_path + "\\icons\\zoho_green.ico"
        menu = (("Check Out", self.red_icon, sys.exit),)
        self.systray = SysTrayIcon(self.red_icon, 'Startup', menu_options=menu)
        self.systray.start()
        self.toast = ToastNotifier()
        self.time_passed = None

    # Crawler begins here.
    # input_row list will contain a single tab separated input from the input_file
    def initiate(self, input_row, region, proxies_from_tool, thread_name):
        self.logger.info(f"Session restore started. Opening Zoho")
        data, driver = general.get_url2(url='https://mail.zoho.com',
                                        tag_to_find='//a[@class="zgh-login"]',
                                        close_session=False, images=True)
        if general.wait_driver(driver, '//a[@class="zgh-login"]', 5):
            self.logger.info("Logging in")
            driver = self.automated_login(driver)
        if general.wait_driver(driver, '//button/span[@class="zmbtn__text" and contains(text(),"New Mail")]', 10):
            self.logger.info("Logged in")
        else:
            self.logger.info("Log in failed")
            print("EXECUTION FAILED CONTACT PACK8 TECH")

    def automated_login(self, driver):
        general.click(driver, '//a[@class="zgh-login"]')
        general.wait_driver(driver, '//button[@id="nextbtn" and @class="btn blue"]', 60)
        self.logger.info(f"Zoho Email")
        general.send_text(driver, secrets["email"],
                          '//input[@id="login_id" and @name="LOGIN_ID"]', 0, click=True)
        time.sleep(5)
        if general.wait_driver(driver, '//input[@id="password"]', 30):
            general.send_text(driver, secrets["password"],
                              '//input[@id="password"]', 0, click=True)
            if general.wait_driver(driver, '//input[@id="mfa_otp"]', 10):
                verfied = False
                while not verfied:
                    print("PLEASE ENTER THE OTP AND CLICK VERIFY")
                    if general.wait_driver(driver,
                                           '//button/span[@class="zmbtn__text" and contains(text(),'
                                           '"New Mail")]',
                                           10):
                        verfied = True
                        return driver
                    if general.wait_driver(driver, '//button[@class="btn blue trustdevice trustbtn"]', 10):
                        general.click(driver, '//button[@class="btn blue trustdevice trustbtn"]')
                        if general.wait_driver(driver,
                                               '//button[@class="btn green"]', 10):
                            general.click(driver, '//button[@class="btn green"]')
        if general.wait_driver(driver, '//button/span[@class="zmbtn__text" and contains(text(),"New Mail")]', 10):
            return driver

    def notify(self, notification, icon, notify=False):
        if notify:
            self.toast.show_toast(
                "Zoho Punch",
                notification,
                duration=5,
                icon_path=icon,
                threaded=True,
            )

    def update_punch(self, punch_time, punch_type, message, notify=False):
        if punch_type == "punchIn":
            dump_file = "zoho_punched_in"
            remove_file = "zoho_punched_out"
            icon = self.green_icon
        else:
            dump_file = "zoho_punched_out"
            remove_file = "zoho_punched_in"
            icon = self.red_icon
        pickle.dump(punch_time, open(dump_file, 'wb'))
        os.remove(remove_file)
        self.systray.update(icon, message)
        self.notify(message, icon, notify)
if __name__ == "__main__":
    crawl = Crawler(current_path)
    crawl.start(crawl.initiate)

    # crawl.punch("punchIn")
