from APIs.webUtils import WebUtils 
import requests
from time import sleep
from pprint import pprint
import mercari
import json
from random import randint
from confings.Consts import ShipmentPriceType as spt
from selenium.webdriver.common.by import By
from traceback import print_exc
from APIs.posredApi import PosredApi


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

        posredCommission = PosredApi.getСommissionForItem(item['page'])
        if PosredApi.isPercentCommision(posredCommission):
            item['posredCommission'] = f"{item['itemPrice']}*{posredCommission['value']/100}"
            item['posredCommissionValue'] = item['itemPrice']*(posredCommission['value']/100)
        else:
            item['posredCommission'] = posredCommission['value']

        return item
    
    @staticmethod
    def parseMandarake(url):
        """Получение базовой информации о лоте со вторички Mandarake

        Args:
            url (string): ссылка на лот

        Returns:
            dict: словарь с информацией о лоте
        """

        item = {}
        
        ok = WebUtils.getSelenium()
        ok.implicitly_wait(5)

        # у манды оч странная херота - просто открыть страницу без рефера не получится (либо я лохушка)
        ok.open("https://www.mandarake.co.jp")
        ok.open("https://order.mandarake.co.jp/order/?lang=en")
        ok.open(url)

        try:
            # хз как иначе вытащить картинку товара
            img = ok.find_element(By.ID, "elevate_zoom").get_attribute("src")
            pprint(img)

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
                item['siteName'] = 'Mandarake'  

                posredCommission = PosredApi.getСommissionForItem(item['page'])
                if PosredApi.isPercentCommision(posredCommission):
                    item['posredCommission'] = f"{item['itemPriceWTax']}*{posredCommission['value']/100}"
                    item['posredCommissionValue'] = item['itemPriceWTax']*(posredCommission['value']/100)
                else:
                    item['posredCommission'] = posredCommission['value']
        except:
            pprint('cant get item info.')
            print_exc()
        finally:
            ok.quit()
            return item