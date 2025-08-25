from bs4 import BeautifulSoup
from confings.Consts import LINUX_USER_AGENT
from selenium.webdriver.support.ui import WebDriverWait
import cfscrape
from seleniumbase import Driver
import requests
import time
from pprint import pprint
import random
from selenium.common.exceptions import TimeoutException

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
    def getSoup(url = '', rawText = '', timeout = 0, parser = Bs4Parsers.htmlParser, isSeleniumNeeded = False, proxyServer = '', isUcSeleniumNeeded = False):
        """Получить bs4 soup по заданной ссылке

        Args:
            url (string): ссылка на страницу
            timeout (int, optional): таймаут. Defaults to 0.
            parser (string, optional): парсер для bs4. Defaults to Bs4Parsers.htmlParser.
            isSeleniumNeeded(bool, optional): использование selenium вместе requests

        Returns:
            bs4.BeautifulSoup: bs4 soup
        """
        if isSeleniumNeeded:
            browser = WebUtils.getSelenium()
            browser.get(url)
            soup = BeautifulSoup(browser.page_source, parser)
            browser.quit()
        elif isUcSeleniumNeeded:
            browser = WebUtils.getSelenium(isUC=True, proxy = proxyServer)
            browser.get(url)

            time.sleep(15)
  
            soup = BeautifulSoup(browser.page_source, parser)
            browser.quit()
        else:    
            if url:
                headers = { 'User-Agent': LINUX_USER_AGENT}
                if proxyServer:
                    page = requests.get(url, headers, proxies={'http': f'http://{proxyServer}'})
                else:
                    page = requests.get(url, headers)
                # где-то таймаут был 20
                soup = BeautifulSoup(page.text, parser)
            elif rawText:
                soup = BeautifulSoup(rawText, parser)
        return soup
    
    @staticmethod
    def wait_for_page_update(driver, timeout=10):
        """Дождаться обновления страницы

        Args:
            driver (seleniumwire.webdriver.Chrome): драйвер
            timeout (int, optional): таймаут. Defaults to 10.

        Returns:
            bool: флаг прогрузки
        """
        try:
            # Ждем пока страница полностью загрузится
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            print("Страница не загрузилась за отведенное время")
            return False

    @staticmethod
    def getSelenium(isUC = False, proxy = '', wire = True, incognito = True):
        """получить веб-драйве

        Args:
            proxy_server (str, optional): Прокси сервер. Defaults to ''.

        Returns:
            seleniumwire.webdriver.Chrome: веб-драйвер
        """
        if proxy:
            return Driver(uc=True, incognito= incognito, proxy = proxy) if isUC else Driver(incognito= incognito, wire=wire, proxy  = proxy)
        else:
            return Driver(uc=True, incognito= incognito) if isUC else Driver(incognito= incognito, wire=wire)
    
    @staticmethod
    def getScraperSessoin(session):

        scraper=cfscrape.create_scraper(sess=session, delay=10)
        #scraper = cfscrape.CloudflareScraper() 
        return scraper
    
    @staticmethod
    def getSraper(url):
        """Получить bs4 soup по заданной ссылке в обход CloudflareScraper

        Args:
            url (string): ссылка на страницу

        Returns:
             bs4.BeautifulSoup: bs4 soup
        """

        def getSraperSoup(response):

            return BeautifulSoup(response.text, WebUtils.Bs4Parsers.htmlParser)

        #scraper = cfscrape.create_scraper()  # returns a CloudflareScraper instance
        session = requests.Session()
        session.headers = WebUtils.getHeader()
        scraper = cfscrape.CloudflareScraper() 
        response = scraper.get(url)

        return getSraperSoup(response)
    
    def getProxyServer(type_needed = ['http']):
        """Получить список прокси с гита

        Args:
            type_needed (list, optional): нужный тип прокси. Defaults to ['http'].

        Returns:
            list: список прокси
        """

        print('getting proxies')
     
        #curl = f'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/json/proxies.json' ['http', 'https']
        curl = 'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/{}.txt'
        #curl = 'https://raw.githubusercontent.com/mmpx12/proxy-list/master/{}.txt'

        proxy_list = [] 
        for type in type_needed:
           
            page = requests.get(curl.format(type), headers = WebUtils.getHeader())
            proxy_list_raw = page.text.split('\n')
            proxy_list.extend(proxy_list_raw)

        proxy_list = list(set(proxy_list))   

        print(f'got {len(proxy_list)} proxies') 

        return proxy_list
    
    def getRandomProxy():
        
        return random.choice(WebUtils.getProxyServer())

    def cleanUrl(url):
        """Почистить ссылку от лишних символов

        Args:
            url (stirng): ссылка

        Returns:
            stirng: очищенная ссылка
        """

        cleaned_url = url
        if cleaned_url.find('/?') > -1:
            cleaned_url = cleaned_url.split('/?')[0]
        if cleaned_url.find('/ref=') > -1:
            cleaned_url = cleaned_url.split('/ref=')[0]        
        return cleaned_url
    
