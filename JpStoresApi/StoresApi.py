from APIs.webUtils import WebUtils 
import requests
from time import sleep
from pprint import pprint
from confings.Consts import ShipmentPriceType as spt
from APIs.posredApi import PosredApi

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
        pprint(soup.contents)
        name = soup.find('div', class_='item_overview_detail').find('h1').text
        price = int(soup.find('p', class_='price new_price fl_l').text.replace(',', '').split('円')[0])
        qnty = int(soup.find('input', id='lot')['value'])
        img = soup.find('div', class_='item_thumbs_inner').find('img')['src']

        item = {}
        item['itemPrice'] = price * qnty
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = spt.undefined
        item['page'] = curl
        item['mainPhoto'] = img
        item['siteName'] = 'Animate'
        item['name'] = name

        posredCommission = PosredApi.getСommissionForItem(item['page'])
        if PosredApi.isPercentCommision(posredCommission):
            item['posredCommission'] = f"{int(item['itemPrice'])}*{posredCommission['value']/100 if posredCommission['value'] > 0 else 0}"
            item['posredCommissionValue'] = item['itemPrice']*(posredCommission['value']/100)
        else:
            item['posredCommission'] = posredCommission['value']          

        return item
        


