from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
#import chromedriver_autoinstaller as chromedriver old
from pyvirtualdisplay import Display
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from confings.Consts import LINUX_USER_AGENT
import cfscrape

import requests

from pprint import pprint

class WebUtils:

    @staticmethod
    def getHeader():
        """Установка заголовков для запросов

        Returns:
            dict: основные настройки заголовков
        """

        headers = {
            'User-Agent': LINUX_USER_AGENT,
            'Content-Type': 'application/json, text/plain, */*',
            'x-platform': 'web',
        }

        return headers
    
    class Bs4Parsers():
        """Парсеры для bs4
        """

        lxml = 'lxml'
        htmlParser = 'html.parser'

    @staticmethod
    def getSoup(url, timeout = 0, parser = Bs4Parsers.htmlParser):
        """Получить bs4 soup по заданной ссылке

        Args:
            url (string): ссылка на страницу
            timeout (int, optional): таймаут. Defaults to 0.
            parser (string, optional): парсер для bs4. Defaults to Bs4Parsers.htmlParser.

        Returns:
            bs4.BeautifulSoup: bs4 soup
        """

        headers = { 'User-Agent': LINUX_USER_AGENT}

        page = requests.get(url, headers)
        # где-то таймаут был 20

        soup = BeautifulSoup(page.text, parser)
        return soup

    @staticmethod
    def getSelenium(isDisplayed = False):
        """получить веб-драйвер

        Returns:
            seleniumwire.webdriver.Chrome: веб-драйвер
        """

        options = Options()

        options.add_argument('--no-sandbox')

        if isDisplayed:
            options.add_argument(f'user-agent={LINUX_USER_AGENT}')
            return webdriver.Chrome(options=options)
            
        options.add_argument("--headless=new") 
        options.add_argument('--disable-dev-shm-usage') 
        options.add_argument(f'user-agent={LINUX_USER_AGENT}')


        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
 
    @staticmethod
    def getDisplay():
        """получить виртуальное окно браузера

        Returns:
            pyvirtualdisplay.display.Display: виртуальное окно браузера
        """

        return Display(visible=0, size=(800, 600))
    
    @staticmethod
    def getSraper(url):

        def getSraperSoup(response):

            return BeautifulSoup(response.text, WebUtils.Bs4Parsers.htmlParser)

        #scraper = cfscrape.create_scraper()  # returns a CloudflareScraper instance
        session = requests.Session()
        session.headers = WebUtils.getHeader()
        scraper = cfscrape.CloudflareScraper()  # CloudflareScraper inherits from requests.Session
        response = scraper.get(url)
        pprint(response)
        return getSraperSoup(response)
