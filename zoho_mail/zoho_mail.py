import json
import os
import pickle
import random
import re
import sys
import time
from base64 import b64encode, b64decode
from datetime import datetime, date
from datetime import timedelta
from random import randrange

import panacea_crawl.general as general
import pandas as pd
import requests
from PIL import Image
from infi.systray import SysTrayIcon
from panacea_crawl.panacea_crawl import Spider
from selenium.webdriver.common.by import By
from win10toast import ToastNotifier

current_path = os.path.dirname(os.path.abspath(__file__))


def configure_credentials():
    if os.path.exists("secrets.json"):
        secrets = json.loads(open("secrets.json", "r").read())
        secrets["password"] = b64decode(secrets["password"]).decode("utf8")
    else:
        email = input("Please enter correct email address:")
        password = input("Please enter correct password:")
        secrets = {
            "email": email,
            "password": password,
        }
        with open("secrets.json", "w") as fw:
            fw.write(
                json.dumps(
                    {
                        "email": email,
                        "password": b64encode(password.encode("utf8")).decode("utf8"),
                    }
                )
            )
    return secrets


def read_input():
    try:
        df = pd.read_excel("input_file.xlsx")
        to_list = list(zip(df.List, df.Name))
        subject = df.Subject.iloc[0]
        body = df.Body.iloc[0]
        # try:
        #     start_datetime = df["Start Datetime"].iloc[0].to_pydatetime()
        #     end_datetime = df["End Datetime"].iloc[0].to_pydatetime()
        #     if start_datetime < datetime.now():
        #         print("START DATETIME CANT BE OLDER THAN CURRENT TIME. PLEASE FIX IT.")
        #         sys.exit(1)
        #     if start_datetime > end_datetime:
        #         print("END DATETIME CANT BE OLDER THAN START DATETIME. PLEASE FIX IT.")
        #         exit(1)
        # except Exception as e:
        #     print(
        #         "INCORRECT DATEFORMAT IN START OR END DATETIME. CORRECT DATEFORMAT: DD-MM-YYYY HH:MM"
        #     )
        #     exit(1)
        interval = df["Email Interval"].iloc[0]
        return to_list, subject, body, start_datetime, end_datetime, interval
    except Exception as e:
        print(f"READING EXCEL FAILED CONTACT PACK8 TECH: {general.get_error_line(e)}")
        exit(1)


def random_date(start, end):
    """
    This function will return a random datetime between two datetime
    objects.
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)


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
        self.systray = SysTrayIcon(self.red_icon, "Startup", menu_options=menu)
        self.systray.start()
        self.toast = ToastNotifier()
        self.time_passed = None
        self.secrets = configure_credentials()
        (
            self.to_list,
            self.subject,
            self.body_template,
            self.start_datetime,
            self.end_datetime,
            self.interval,
        ) = read_input()

    # Crawler begins here.
    # input_row list will contain a single tab separated input from the input_file
    def initiate(self, input_row, region, proxies_from_tool, thread_name):
        data, driver = general.get_url2(
            url="https://mail.zoho.com",
            tag_to_find='//a[@class="zgh-login"]',
            close_session=False,
            images=True,
        )
        if general.wait_driver(driver, '//a[@class="zgh-login"]', 5):
            self.logger.info("Logging in")
            driver = self.automated_login(driver)
        if general.wait_driver(
            driver,
            '//button/span[@class="zmbtn__text" and contains(text(),"New Mail")]',
            10,
        ):
            self.logger.info("Logged in")
            self.send_emails(self.to_list, self.subject, self.body_template, driver)
        else:
            self.logger.info("Log in failed")
            print("EXECUTION FAILED CONTACT PACK8 TECH")

    def send_emails(self, to_list, subject, body_template, driver):
        print("Sending emails:")
        total = len(to_list)
        for i, recipient in enumerate(to_list):
            print(f"({i+1}/{total}) {recipient[1]} - {recipient[0]}")
            if recipient[0] and recipient[1]:
                body = body_template.replace("$name", recipient[1])
                general.click(
                    driver,
                    '//button/span[@class="zmbtn__text" and contains(text(),"New Mail")]',
                )
                if general.wait_driver(
                    driver,
                    '//div[@class="SCm"]//div[@class="zmCRow" and ./font/span[contains(text(),"To")]]//input[@type="text"]',
                    10,
                ):
                    general.send_text(
                        driver,
                        recipient[0],
                        '//div[@class="SCm"]//div[@class="zmCRow" and ./font/span[contains(text(),"To")]]//input[@type="text"]',
                        click=True,
                    )
                    general.send_text(
                        driver,
                        subject,
                        '//div[@class="SCm"]//div[contains(@class, "subject-field")]/input',
                        click=True,
                    )
                    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
                        driver.switch_to.frame(iframe)
                        if general.find_elements_driver(
                            driver,
                            '//body[@contenteditable="true" and .//div[@class="zmail_signature_below"]]',
                        ):
                            break
                        else:
                            driver.switch_to.parent_frame()
                    body_div = driver.find_element(
                        By.XPATH,
                        '//body[@contenteditable="true" and .//div[@class="zmail_signature_below"]]',
                    )
                    body_div.clear()
                    for line in body.split("\n"):
                        new_line = "\n\n" if line else "\n"
                        body_div.send_keys(line)
                        body_div.send_keys(new_line)
                    driver.switch_to.parent_frame()
                    time.sleep(3)
                    general.click(driver, '//button[@aria-label="Send"]')
                    time.sleep(self.interval * 60)
                    # general.click(driver, '//div[@class="SCm"]//i[@class="msi-schdRecur zmbtn__icon "]')
                    # while not ('//section[@class="//section[@class="zmdialog zmdialog--md zmdialog--top zmail-schdlrcrrng"]//span[@class="zmradio"]/input[@value="custom"]'):
                    #     time.sleep(3)
                    # while not general.find_elements_driver(driver, '//span[@data-placeholder="Select Date"]'):
                    #     time.sleep(1)
                    #     general.click(driver,
                    #                   '//section[@class="zmdialog zmdialog--md zmdialog--top '
                    #                   'zmail-schdlrcrrng"]//span[@class="zmradio"]/input[@value="custom"]')
                    # random_datetime = random_date(self.start_datetime, self.end_datetime)
                    # general.set_tag_innerhtml_driver(driver, '//span[@data-placeholder="Select Date"]', random_datetime.strftime("%d/%m/%Y"))
                    # time.sleep(2)
                    # general.set_tag_attribute_driver(driver, '//div[@class="zmdp__time__hour"]//input[@aria-valuemax="23"]', 'value', str(random_datetime.hour))
                    # general.set_tag_attribute_driver(driver, '//div[@class="zmdp__time__hour"]//input[@aria-valuemax="23"]', 'aria-valuenow', str(random_datetime.hour))
                    # general.set_tag_attribute_driver(driver, '//div[@class="zmdp__time__hour"]//input[@aria-valuemax="23"]', 'aria-valuetext', str(random_datetime.hour))
                    # general.set_tag_attribute_driver(driver,
                    #                                  '//div[@class="zmdp__time__hour"]//input['
                    #                                  '@aria-valuemax="59"]',
                    #                                  'value', str(random_datetime.minute))
                    # general.set_tag_attribute_driver(driver,
                    #                                  '//div[@class="zmdp__time__hour"]//input['
                    #                                  '@aria-valuemax="59"]',
                    #                                  'aria-valuenow', str(random_datetime.minute))
                    # general.set_tag_attribute_driver(driver,
                    #                                  '//div[@class="zmdp__time__hour"]//input[@aria-valuemax="59"]',
                    #                                  'aria-valuetext', str(random_datetime.minute))
                    # general.click(driver, '//span[contains(text(), "Schedule and Send")]')
                    # time.sleep(3)

    def automated_login(self, driver):
        general.click(driver, '//a[@class="zgh-login"]')
        general.wait_driver(driver, '//button[@id="nextbtn" and @class="btn blue"]', 60)
        self.logger.info(f"Zoho Email")
        general.send_text(
            driver,
            self.secrets["email"],
            '//input[@id="login_id" and @name="LOGIN_ID"]',
            0,
            click=True,
        )
        time.sleep(5)
        while not general.wait_driver(driver, '//input[@id="password"]', 5):
            time.sleep(1)
        if general.wait_driver(driver, '//input[@id="password"]', 30):
            general.send_text(
                driver,
                self.secrets["password"],
                '//input[@id="password"]',
                0,
                click=True,
            )
            if general.wait_driver(driver, '//input[@id="mfa_otp"]', 10):
                verfied = False
                while not verfied:
                    print("PLEASE ENTER THE OTP AND CLICK VERIFY")
                    if general.wait_driver(
                        driver,
                        '//button/span[@class="zmbtn__text" and contains(text(),'
                        '"New Mail")]',
                        10,
                    ):
                        verfied = True
                        return driver
                    if general.wait_driver(
                        driver, '//button[@class="btn blue trustdevice trustbtn"]', 10
                    ):
                        general.click(
                            driver, '//button[@class="btn blue trustdevice trustbtn"]'
                        )
                        if general.wait_driver(
                            driver, '//button[@class="btn green"]', 10
                        ):
                            general.click(driver, '//button[@class="btn green"]')
        if general.wait_driver(
            driver,
            '//button/span[@class="zmbtn__text" and contains(text(),"New Mail")]',
            10,
        ):
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
        pickle.dump(punch_time, open(dump_file, "wb"))
        os.remove(remove_file)
        self.systray.update(icon, message)
        self.notify(message, icon, notify)


if __name__ == "__main__":
    crawl = Crawler(current_path)
    crawl.start(crawl.initiate)

    # crawl.punch("punchIn")
