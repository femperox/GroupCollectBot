from APIs.webUtils import WebUtils 
import requests
from time import sleep
from pprint import pprint
import mercari
import json
from random import randint
from confings.Consts import ShipmentPriceType as spt
from selenium.webdriver.common.by import By



class SecondaryStoreApi:

    @staticmethod
    def parsePayPay(url, item_id):
        """Получение базовой информации о лоте со вторички PayPay

        Args:
            url (string): ссылка на лот
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        curl = f'https://paypayfleamarket.yahoo.co.jp/api/item/v2/items/{item_id}'
        print(curl)

        headers = WebUtils.getHeader()
        page = requests.get(curl, headers=headers)
        js = page.json()

        item = {}
        item['itemPrice'] = js['price']
        item['tax'] = 0
        item['itemPriceWTax'] = 0 # всегда включено в цену
        item['shipmentPrice'] = spt.free
        item['page'] = url
        item['mainPhoto'] = js['images'][0]['url']
        item['siteName'] = 'payPayFleamarket'

        return item
    
    @staticmethod
    def parseMercariPage(url, item_id):
        """Получение базовой информации о лоте со вторички mercari

        Args:
            url (string): ссылка на лот
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        session = requests.session()
        curl = f'https://api.mercari.jp/items/get?id={item_id}'

        headers = WebUtils.getHeader()
        headers['Content-Type'] = ''
        headers['DPOP'] = mercari.generate_DPOP(uuid=f"{randint(0,100)}{item_id}", method="GET", url=curl)

        page = session.get(curl, headers=headers)
        js = page.json() 

        item = {}
        item['itemPrice'] = js['data']['price']
        item['tax'] = 0
        item['itemPriceWTax'] = 0 # Всегда включена в цену
        item['shipmentPrice'] = spt.free if js['data']['shipping_payer']['id'] == 2 else spt.undefined
        item['page'] = url
        item['mainPhoto'] = js['data']['photos'][0]
        item['siteName'] = 'mercari'

        return item
    
    @staticmethod
    def parseMandarake(url):
        """Получение базовой информации о лоте со вторички Mandarake

        Args:
            url (string): ссылка на лот

        Returns:
            dict: словарь с информацией о лоте
        """
        item = ''
        proxyServers = WebUtils.getProxyServer(country='JP')
        
        pprint(proxyServers)
        for proxyServer in proxyServers:
            
            ok = WebUtils.getSelenium(proxyServer=proxyServer)
            ok.implicitly_wait(30)
            ok.get(url)

            try:
                img = ok.find_element(By.ID, "elevate_zoom").get_attribute("src")
                pprint(img)
            except:
                pprint(f'{proxyServer} cant get img. getting another one proxy')
                continue

            info = ''
            for request in ok.requests:
                if request.url.find('getInfo') > 0:
                    info = request.response.body

            if not info:
                pprint(f'{proxyServer} cant get info. getting another one proxy')
                continue

            info = json.loads(info.decode('utf8'))
            pprint(type(info))
            item = ''
            item['itemPrice'] = info['price']
            item['itemPriceWTax'] = info['price_with_tax']
            item['tax'] = item['itemPriceWTax'] * 100 / item['priceYen']
            item['shipmentPrice'] = spt.undefined
            item['page'] = url
            item['mainPhoto'] = img
            item['siteName'] = 'Mandarake'
        
            break

        return item