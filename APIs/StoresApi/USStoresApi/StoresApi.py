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
    def getInfo(curl, url, storeName, variant = None, priceForFreeShipment = None, shipmentPrice = None):
        """Получить инфо из js запроса по шаблону

        Args:
            curl (string): ссылка на js-скрипт
            url (string): ссылка на товар
            storeName (string): название магазина
            variant (string, optional): вариант товара. Defaults to None.
            priceForFreeShipment (int, optional): цена заказа для бесплатной доставки. Defaults to None.
            shipmentPrice (int, optional): цена доставки. Defaults to None.

        Returns:
            dict: словарь с информацией о товаре
        """

        headers = WebUtils.getHeader()
        page = requests.get(curl, headers=headers)
        js = page.json() 

        item = {}

        item['itemPrice'] = float(js['price'])/100
        item['id'] = js['id']

        item['tax'] = 0
        item['itemPriceWTax'] = 0
        if priceForFreeShipment is None:
            item['shipmentPrice'] = ShipmentPriceType.undefined if shipmentPrice is None else shipmentPrice
        else:
            item['priceForFreeShipment'] = priceForFreeShipment
            item['shipmentPrice'] = ShipmentPriceType.undefined if shipmentPrice is None else shipmentPrice
            item['shipmentPrice'] = ShipmentPriceType.free if item['itemPrice'] >= item['priceForFreeShipment'] else item['shipmentPrice']
                    
        item['page'] = url

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

        item['name'] = js['title']
        item['endTime'] = datetime.now() + relativedelta(years=3)
        item['siteName'] = storeName

        commission = PosredApi.getСommissionForItemUSD()

        format_string = item['itemPrice']
        format_number = item['itemPrice']
        item['posredCommission'] = commission['posredCommission'].format(format_string)
        item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)
        
        return item
    @staticmethod
    def parseFangamerItem(url):
        """Получение базовой информации о товаре с магазина fangamer

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """

        curl = f'https://www.fangamer.com/products/{url.split("products/")[-1]}.js'
        item = StoresApi.getInfo(curl = curl, url = url, storeName = Stores.fangamer)
        return item

    @staticmethod
    def parseBratzItem(url):
        """Получение базовой информации о товаре с магазина bratz

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """

        curl = f'https://www.bratz.com/products/{url.split("products/")[-1]}.js'
        item = StoresApi.getInfo(curl = curl, url = url, priceForFreeShipment = 50, storeName = Stores.bratz)
        return item

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
        """Получение базовой информации о товаре с магазина plushShop

        Args:
            url (string): ссылка на товар
            item_id (string): id товара

        Returns:
            dict: словарь с информацией о товаре
        """

        variant = None
        if item_id.find('?variant=') > -1:
            curl = f'https://www.plushshop.com/collections/anime-meow/products/{item_id.split("?variant=")[0]}.js'
            variant = int(item_id.split("?variant=")[1])
        else:
            curl = f'https://www.plushshop.com/collections/anime-meow/products/{item_id}.js'
  
        item = StoresApi.getInfo(curl = curl, variant = variant, url = url, 
                                 priceForFreeShipment = 79.99, shipmentPrice = 15, storeName = Stores.plushshop)
        return item
    
    @staticmethod
    def parseHotTopicItem(url):

        bs = WebUtils.getSoup(url = url, proxyServer = '212.6.44.158:53298', isUcSeleniumNeeded = True)
        pprint(bs.text)