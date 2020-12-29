import zipfile
import random
import urllib
import os
import re
import string
import time
import glob
import requests
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver import Chrome, ChromeOptions

SESSION_COUNT = 2
PAGE_URL = 'https://direct.playstation.com/en-us/ps5'

def get_driver(chromedriver_path) -> None:
    chromedriver_path = f'{os.getcwd()}/chromedriver.exe'
    chromedriver_archive = chromedriver_path.replace('.exe', '.zip')
    latest = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE')
    chromedriver = urllib.request.urlretrieve(f'https://chromedriver.storage.googleapis.com/{latest.text}/chromedriver_win32.zip', chromedriver_archive)
    with zipfile.ZipFile(chromedriver_archive, 'r') as zip_ref:
        zip_ref.extractall('.')
    os.remove(chromedriver_archive)

class BruteForceBot:

    def __init__(self, chromedriver_path: str) -> None:
        self.driver_file = self.change_driver(chromedriver_path)
        assert self.driver_file
        self.start_browser()
        self.alive = True

    def start_browser(self) -> None:
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "eager"
        chrome_options = ChromeOptions()
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        driver = Chrome(desired_capabilities=caps, executable_path=self.driver_file, options=chrome_options)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
            Object.defineProperty(window, 'navigator', {
                value: new Proxy(navigator, {
                has: (target, key) => (key === 'webdriver' ? false : key in target),
                get: (target, key) =>
                    key === 'webdriver'
                    ? undefined
                    : typeof target[key] === 'function'
                    ? target[key].bind(target)
                    : target[key]
                })
            })
                    """
            },
        )
        self.driver = driver

    def change_driver(self, driver_file: str) -> str:
        with open(driver_file, 'rb') as fin:
            data = fin.read()
            cdc_path = f'${"".join(random.choices(string.ascii_lowercase, k=3))}_{"".join(random.choices(string.ascii_letters + string.digits, k=22))}_'
            result = re.search(b"[$][a-z]{3}_[a-zA-Z0-9]{22}_", data)
            if result is not None:
                try:
                    data = data.replace(result.group(0), cdc_path.encode())
                    fin.close()
                    fin = open(f'./drivers/chromedriver_{cdc_path[1:-1]}.exe', 'wb')
                    fin.truncate()
                    fin.write(data)
                    return f'./drivers/chromedriver_{cdc_path[1:-1]}.exe'
                except:
                    return ''
    
    def heartbeat(self) -> None:
        try:
            _ = self.driver.window_handles
        except:
            self.alive = False
    
    def cleanup(self) -> None:
        try:
            self.driver.close()
        except:
            pass
        self.driver.quit()

if __name__ == '__main__':
    chromedriver_path = f'{os.getcwd()}/chromedriver.exe'
    if not os.path.isdir('./drivers'):
        os.mkdir('./drivers')
    drivers = []
    if not os.path.exists(chromedriver_path):
        get_driver(chromedriver_path)
    for i in range(SESSION_COUNT):
        drivers.append(BruteForceBot(chromedriver_path))
    for driver in drivers:
        driver.driver.get(PAGE_URL)
    done = False
    while not done:
        time.sleep(5)
        [driver.heartbeat() for driver in drivers]
        done = not any([driver.alive for driver in drivers])
    [driver.cleanup() for driver in drivers]
    for f in glob.glob('./drivers/chromedriver*.exe'):
        os.remove(f)
    
