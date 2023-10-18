from APIs.webUtils import WebUtils 
import requests
from time import sleep
from pprint import pprint

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
        item['shipmentPrice'] = 0 # всегда бесплатная
        item['page'] = url
        item['mainPhoto'] = js['images'][0]['url']
        item['siteName'] = 'payPayFleamarket'

        return item
    
    @staticmethod
    def parseMercariPage(url, item_id, dpop):
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
        #headers[':authority:'] = 'jp.mercari.com'
        # не робит на линуксе. искать обходняк, либо тупо bs4

        
        ok = WebUtils.getSelenium()
        
        ok.get(url)
        ok.implicitly_wait(30) # seconds
        pprint(ok.requests)
   
        
        '''
        ok = requests.get(url, headers)   
        pprint(ok.status_code)
        pprint(ok.content)
        '''

        '''    
        dpop = ''
        for request in ok.requests:
            if request.url.find('get?id=')>0:
                dpop = request.headers['dpop']

        pprint(dpop)
        

        headers = WebUtils.getHeader()
        # Чекнуть когд он просрочится
        headers['dpop'] = dpop
        
        page = session.get(curl, headers=headers)
        js = page.json()

        pprint(js)

        item = {}
        item['itemPrice'] = js['data']['price']
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = 0
        item['page'] = url
        item['mainPhoto'] = js['data']['photos'][0]
        item['siteName'] = 'mercari'
        '''
        item = ''
        return item
    
    def parseMandarake(url):
        """Получение базовой информации о лоте со вторички Mandarake

        Args:
            url (string): ссылка на лот

        Returns:
            dict: словарь с информацией о лоте
        """

        ok = WebUtils.getSelenium()

        # не робит на линуксе. искать обходняк, либо тупо bs4
        ok.implicitly_wait(40)
        ok.get(url)

        for request in ok.requests:
            if request.url.find('getInfo') > 0:
                info = request.response.body

        pprint(ok.requests)
        pos_tax = str(info).find('"price_with_tax":')
        pos_price = str(info).find('"price":')
        pos_segment = str(info).find(',"segment')


        item = {}
        '''
        item['itemPrice'] = int(str(info)[pos_price+len('"price":'):pos_segment])
        item['itemPriceWTax'] = int(str(info)[pos_tax+len('"price_with_tax":'):-2]) - item['priceYen']
        item['tax'] = item['itemPriceWTax'] * 100 / item['priceYen']
        item['shipmentPrice'] = 0
        item['page'] = url
        #item['mainPhoto'] = додумать
        item['siteName'] = 'Mandarake'
        '''
        return item