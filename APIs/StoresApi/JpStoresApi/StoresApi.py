from APIs.webUtils import WebUtils 
import requests
from confings.Consts import OrdersConsts
from datetime import datetime
from dateutil.relativedelta import relativedelta
from time import sleep
from pprint import pprint
from APIs.PosredApi.posredApi import PosredApi

class StoreApi:

    @staticmethod
    def parseAnimate(item_id):
        """Получение базовой информации о лоте с магазина Animate

        Args:
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        curl = f'https://www.animate-onlineshop.jp/pd/{item_id}/'

        soup = WebUtils.getSoup(curl)

        name = soup.find('div', class_='item_overview_detail').find('h1').text
        price = int(soup.find('p', class_='price new_price').text.replace(',', '').split('円')[0])
        qnty = int(soup.find('input', id='lot')['value'])
        img = soup.find('div', class_='item_thumbs_inner').find('img')['src']

        item = {}
        item['itemPrice'] = price * qnty
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
        item['page'] = curl
        item['mainPhoto'] = img
        item['name'] = name

        commission = PosredApi.getСommissionForItem(item['page'])
        item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
        item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice'])

        item['siteName'] = OrdersConsts.Stores.animate
        item['id'] = item_id           

        return item
    
    @staticmethod
    def parseBooth(url):

        curl = url.replace('/en/', '/ja/') +'.json'

        headers = WebUtils.getHeader()
        page = requests.get(curl, headers=headers)

        js = page.json()
        item = {}
        try:
            pprint(js)
            item['id'] = js['id']
            item['mainPhoto'] = js['images'][0]['original']
            item['status'] = OrdersConsts.StoreStatus.sold if js['is_sold_out'] else OrdersConsts.StoreStatus.in_stock
            item['itemPrice'] = float(js['variations'][0]['price'])
            item['name'] = js['variations'][0]['name']
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
            item['page'] = js['url']
            item['siteName'] = OrdersConsts.Stores.booth

        except Exception as e:
            pprint(e)
        finally:
            return item
        


