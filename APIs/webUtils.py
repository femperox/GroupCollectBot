from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
#import chromedriver_autoinstaller as chromedriver old

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
            'User-Agent': ': Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 OPR/86.0.4363.64',
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

        headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36'}

        page = requests.get(url, headers)
        # где-то таймаут был 20

        soup = BeautifulSoup(page.text, parser)
        pprint(type(soup))
        return soup

    @staticmethod
    def getSelenium():
        """получить веб-драйвер

        Returns:
            seleniumwire.webdriver.Chrome: веб-драйвер
        """

        options = Options()

        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        #return webdriver.Chrome(chromedriver.install(), options=options) #old

        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
 
