from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
#import chromedriver_autoinstaller as chromedriver old
from pyvirtualdisplay import Display
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from confings.Consts import LINUX_USER_AGENT
import cfscrape
import pprint

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
    def getSoup(url, timeout = 0, parser = Bs4Parsers.htmlParser, isSeleniumNeeded = False, proxyServer = ''):
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
            browser = WebUtils.getSelenium(proxyServer=proxyServer)
            browser.get(url)
            soup = BeautifulSoup(browser.page_source, parser)
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
    def getSelenium(isDisplayed = False, proxyServer = ''):
        """получить веб-драйве

        Args:
            isDisplayed (bool, optional): дисплейинг. Defaults to False.
            proxy_server (str, optional): Прокси сервер. Defaults to ''.

        Returns:
            seleniumwire.webdriver.Chrome: веб-драйвер
        """

        options = Options()

        options.add_argument('--no-sandbox')

        if proxyServer:
            options.add_argument(f'--proxy-server={proxyServer}')

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
    

    def getProxyServer(country = 'US'):
            
            pprint('getting proxy servers')

            proxy_site = 'https://proxyservers.pro/proxy/list/protocol/http%2Chttps/country/{}/order/updated/order_dir/desc/page/1'

            soup = WebUtils.getSoup(url = proxy_site.format(country), isSeleniumNeeded= True)
            
            result_list_hosts = soup.find_all('a', class_='ajax1 action-dialog-ajax-inact action-modal-ajax-inact')
            result_list_ports = soup.find_all('span', class_='port')

            pprint('got proxy servers')

            return [f'{result_list_hosts[i].text}:{result_list_ports[i].get_text()}' for i in range(len(result_list_hosts))]

    
    def getProxyRequest(url, country = 'US'):

        def make_proxy_entry(proxy_ip_port):  
            return {'http': f'http://{proxy_ip_port}'}

        
        ip_opts = WebUtils.getProxyServer(country = country)

        search_result = None
        for ip_port in ip_opts:
            pprint(ip_port)
            proxy_entry = make_proxy_entry(ip_port)
            try:
                search_result = requests.get(url, headers=WebUtils.getHeader(),
                                            proxies=proxy_entry)
                print('Successfully gathered results')
                pprint(search_result.content)
                break
            except Exception as e:
                print(f'Failed to connect to endpoint, with proxy {ip_port}.\n'
                            f'Details: {e}')
        else:
            print('Never made successful connection to end-point!')
            search_result = None
        
        return 'search_result'
