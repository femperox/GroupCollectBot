from APIs.webUtils import WebUtils 
import requests
from pprint import pprint
from datetime import datetime
import json
from dateutil.relativedelta import relativedelta
from confings.Consts import ShipmentPriceType as spt, Stores
from selenium.webdriver.common.by import By
from traceback import print_exc
from APIs.posredApi import PosredApi
import time


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
        item['endTime'] = datetime.now() + relativedelta(years=3)

        commission = PosredApi.getСommissionForItem(item['page'])
        item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
        item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice'])  

        item['siteName'] = Stores.payPay
        item['id'] = item_id   

        return item
    
    @staticmethod 
    def parseSuruga(url):
        """Получение базовой информации о лоте со вторички suruga-ya.jp

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о лоте
        """
        
        item = {}
        soup = WebUtils.getSoup(url, parser= WebUtils.Bs4Parsers.htmlParser)

        try:
            js = soup.findAll('script', type='application/ld+json')[1].text.replace('\n', '').replace('    ', '')
            js = json.loads(js)[0]
            
            item['itemPrice'] = float(js['offers'][0]['price']) if isinstance(js['offers'], list) else float(js['offers']['price'])
            item['id'] = js['productID']
            item['mainPhoto'] = js['image']
            item['name'] = js['name']
        
        except json.decoder.JSONDecodeError:
            
            item['itemPrice'] =  float(soup.find('span', class_ = 'text-price-detail price-buy').text.split('円')[0].replace(',', ''))
            item['id'] = url.split('detail/')[-1].split('?')[0]
            item['mainPhoto'] = soup.find('img', class_ = 'img-fluid main-pro-img cursor_pointer')['src']
            item['name'] = soup.find('h1', class_ = 'h1_title_product').text.replace('\n', '').replace('         ', '')

        item['shipmentPrice'] = spt.undefined
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['page'] = url
        item['endTime'] = datetime.now() + relativedelta(years=3)
        item['siteName'] = Stores.suruga
        commission = PosredApi.getСommissionForItem(item['page'])
        item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
        item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice']) 

        return item
        
    
    @staticmethod
    def parseMandarake(url, item_id):
        """Получение базовой информации о лоте со вторички Mandarake

        Args:
            url (string): ссылка на лот

        Returns:
            dict: словарь с информацией о лоте
        """

        item = {}
        
        ok = WebUtils.getSelenium()
        # у манды оч странная херота - просто открыть страницу без рефера не получится (либо я лохушка)
        ok.open("https://www.mandarake.co.jp")
        time.sleep(5)
        ok.open("https://www.mandarake.co.jp/index2.html")
        print('ok3')
        time.sleep(5)
        ok.open(url)
        time.sleep(15) 
        
        try:
            # хз как иначе вытащить картинку товара
            img = ok.find_element(By.ID, "elevate_zoom").get_attribute("src")

            info = ''
            for request in ok.requests:
                if request.url.find('getInfo') > 0:
                    info = request.response.body
            
            if info:

                info = json.loads(info.decode('utf8'))

                item['itemPrice'] = info['price']
                item['itemPriceWTax'] = info['price_with_tax']
                item['tax'] = item['itemPriceWTax'] * 100 / item['itemPrice'] - 100
                item['shipmentPrice'] = spt.undefined
                item['page'] = url
                item['mainPhoto'] = img 
                item['endTime'] = datetime.now() + relativedelta(years=3)

                commission = PosredApi.getСommissionForItem(item['page'])
                item['posredCommission'] = commission['posredCommission'].format(item['itemPriceWTax'])
                item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPriceWTax'])  

                item['siteName'] = Stores.mandarake
                item['id'] = item_id   
                
        except:
            pprint('cant get item info.')
            print_exc()
        finally:
            ok.quit()
            return item