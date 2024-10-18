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
        time.sleep(5)
        ok.open(url)
        time.sleep(5)      

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