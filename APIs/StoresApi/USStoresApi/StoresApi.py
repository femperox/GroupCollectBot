from APIs.webUtils import WebUtils 
from pprint import pprint
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from confings.Consts import Stores, ShipmentPriceType
from APIs.posredApi import PosredApi
import requests

class StoresApi:

    @staticmethod
    def parseMakeshipItem(url):
        """Получение базовой информации о товаре с магазина Makeship

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """

        soup = WebUtils.getSoup(url)

        js = soup.findAll('script', type='application/ld+json')[0].text.replace('&quot;','"')
        js = json.loads(js)

        item = {}

        item['itemPrice'] = float(js['offers']['price'])
        item['id'] = js['offers']['url'].split('/')[-1]

        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = 8.99
        item['page'] = url
        item['mainPhoto'] = js['image']
        item['name'] = js['name']
        item['endTime'] = datetime.now() + relativedelta(years=3)
        item['siteName'] = Stores.makeship

        commission = PosredApi.getСommissionForItemUSD()

        format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
        format_number = item['itemPrice'] + item['shipmentPrice']
        item['posredCommission'] = commission['posredCommission'].format(format_string)
        item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)

        return item


    @staticmethod
    def parsePlushShopItem(url, item_id):

        variant = 0
        if item_id.find('?variant=') > -1:
            curl = f'https://www.plushshop.com/collections/anime-meow/products/{item_id.split("?variant=")[0]}.js'
            variant = int(item_id.split("?variant=")[1])
        else:
            curl = f'https://www.plushshop.com/collections/anime-meow/products/{item_id}.js'
  
        page = requests.get(curl)
        js = page.json() 

        item = {}
        
        pprint(js)
    
        if variant:
            variant_item = [x for x in js['variants'] if x['id'] == variant][0]
            item['itemPrice'] = variant_item['price']
            if 'featured_image' in variant_item:
                item['mainPhoto'] = variant_item['featured_image']['src']
            else:
                item['mainPhoto'] = 'https:' + js['featured_image']
            item['name'] = variant_item['name']
        else:
            item['itemPrice'] = js['price']
            item['mainPhoto'] = 'https:' + js['featured_image']
            item['name'] = js['title']

        item['itemPrice'] = float(item['itemPrice'])/100
        item['id'] = js['handle']
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['priceForFreeShipment'] = 79.99
        item['shipmentPrice'] = 0 if item['itemPrice'] >= item['priceForFreeShipment'] else 15
        item['page'] = url
        item['endTime'] = datetime.now() + relativedelta(years=3)
        item['siteName'] = Stores.plushshop

        commission = PosredApi.getСommissionForItemUSD()

        format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
        format_number = item['itemPrice'] + item['shipmentPrice']
        item['posredCommission'] = commission['posredCommission'].format(format_string)
        item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)

        if item['shipmentPrice'] == 0:
            item['shipmentPrice'] = ShipmentPriceType.free

        return item