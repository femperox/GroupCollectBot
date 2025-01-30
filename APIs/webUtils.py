from bs4 import BeautifulSoup
from confings.Consts import LINUX_USER_AGENT
import cfscrape
from seleniumbase import Driver
import requests
import time
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
    def getSoup(url, timeout = 0, parser = Bs4Parsers.htmlParser, isSeleniumNeeded = False, proxyServer = '', isUcSeleniumNeeded = False):
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
            headers = { 'User-Agent': LINUX_USER_AGENT}
            if proxyServer:
                page = requests.get(url, headers, proxies={'http': f'http://{proxyServer}'})
            else:
                page = requests.get(url, headers)
            # где-то таймаут был 20
            soup = BeautifulSoup(page.text, parser)
        return soup

    @staticmethod
    def getSelenium(isUC = False, proxy = ''):
        """получить веб-драйве

        Args:
            proxy_server (str, optional): Прокси сервер. Defaults to ''.

        Returns:
            seleniumwire.webdriver.Chrome: веб-драйвер
        """
        if proxy:
            return Driver(uc=True, incognito= True, proxy = proxy) if isUC else Driver(incognito= True, wire=True, proxy  = proxy)
        else:
            return Driver(uc=True, incognito= True) if isUC else Driver(incognito= True, wire=True)
    
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
