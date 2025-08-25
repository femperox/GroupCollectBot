from APIs.webUtils import WebUtils 
from pprint import pprint
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from confings.Consts import OrdersConsts
from APIs.PosredApi.posredApi import PosredApi
from _utils.dateUtils import DateUtils
import requests
import re

class StoresApi:

    @staticmethod
    def setItemStatus(item_available, tags):
        """Простановка статуса для getInfo

        Args:
            item_available (bool): доступность айтема
            tags (list[str]): список тегов

        Returns:
            OrdersConsts.StoreStatus: общепринятый статус айтема
        """

        if item_available:
                return OrdersConsts.StoreStatus.in_stock
        else:
            if 'coming_soon' in tags: # обычно для youtooz
                return OrdersConsts.StoreStatus.pre_order
            elif 'restocking_soon' in tags: # обычно для fangamer
                return OrdersConsts.StoreStatus.restock
            else:
                return OrdersConsts.StoreStatus.sold

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
        try:
            if variant:
                variant_item = [x for x in js['variants'] if x['id'] == variant][0]
                item['itemPrice'] = variant_item['price']
                if 'featured_image' in variant_item:
                    item['mainPhoto'] = variant_item['featured_image']['src']
                else:
                    item['mainPhoto'] = 'https:' + js['featured_image']
                item['name'] = variant_item['name']

                item['status'] = StoresApi.setItemStatus(item_available = variant_item['available'], tags = js['tags'])

            else:
                if len(js['variants']) > 1 and js['variants'][0]['available'] == False:
                    item['itemPrice'] = js['variants'][-1]['price']
                else:
                    item['itemPrice'] = js['price']
                item['mainPhoto'] = 'https:' + js['featured_image']
                item['name'] = js['title']

                item['status'] = StoresApi.setItemStatus(item_available = js['available'], tags = js['tags'])
            
            item['itemPrice'] = float(item['itemPrice'])/100
            item['id'] = js['id']

            item['tax'] = 0
            item['itemPriceWTax'] = 0
            if priceForFreeShipment is None:
                item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined if shipmentPrice is None else shipmentPrice
            else:
                item['priceForFreeShipment'] = priceForFreeShipment
                item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined if shipmentPrice is None else shipmentPrice
                item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if item['itemPrice'] >= item['priceForFreeShipment'] else item['shipmentPrice']
                        
            item['page'] = url

            item['name'] = js['title']
            item['siteName'] = storeName

            commission = PosredApi.getСommissionForItemUSD()

            format_string = item['itemPrice']
            format_number = item['itemPrice']
            item['posredCommission'] = commission['posredCommission'].format(format_string)
            item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)

        except Exception as e:
            pprint(e)
        finally:
            return item
    
    @staticmethod
    def parseMattelItem(url):
        """Получение базовой информации о товаре с магазина mattel

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """
        
        curl = f'https://creations.mattel.com/products/{url.split("products/")[-1]}.js'
        shipping_price_url = 'https://creations.mattel.com/pages/shipping-rates-policy'

        soup_shipment = WebUtils.getSoup(url = shipping_price_url)
        shipment_price = soup_shipment.find('tbody').findAll('td')[1].text
        shipment_price = float(shipment_price.replace('$', ''))
        
        item = StoresApi.getInfo(curl = curl, url = url, 
                                shipmentPrice = shipment_price,
                                storeName = OrdersConsts.Stores.mattel)
        
        soup = WebUtils.getSoup(url = url)

        if item['status'] == OrdersConsts.StoreStatus.sold:
            for script in soup.find_all("script"):
                target_script = None
                if script.string and "SDG.Data.comingSoon" in script.string:
                    target_script = script.string.strip()
                    break
            if target_script:
                js_start = target_script.find('expiry: "') + len('expiry: "')
                js_end = target_script.find("}") - 1
                preorder_date_expiry = target_script[js_start:js_end].replace('\n', '').replace(',','').replace('"', "'").replace("'", '').strip()
                if DateUtils.compair_dates(date1 = DateUtils.parse_utc_date(text= preorder_date_expiry), date2 = DateUtils.getCurrentDate(need_date_str = False)):
                    item['status'] = OrdersConsts.StoreStatus.pre_order        
                else:
                    return item

        soup_membership_script = soup.find_all('script', {'type': 'text/javascript'})
        target_script = None
        for script in soup_membership_script:
            if script.string and "'item_badge':" in script.string:
                target_script = script.string.strip()
                break
        if target_script:
            js_start = target_script.find("'item_badge':") + len("'item_badge':")
            js_end = target_script.find("'item_bundle_id'") - 1
            membership = target_script[js_start:js_end].replace('\n', '').replace(',','').replace("'", '').strip() if 'Members Only' in script.string else ''
            item['isMembershipNeeded'] = bool(membership)
        
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
        item = StoresApi.getInfo(curl = curl, url = url, storeName = OrdersConsts.Stores.fangamer)

        if item['status'] == OrdersConsts.StoreStatus.sold:
            soup = WebUtils.getSoup(url = url)
            notify = soup.find('div', class_= 'notice').text
            if 'coming soon' in notify.lower():
                item['status'] = OrdersConsts.StoreStatus.pre_order

        return item

    @staticmethod
    def parseBratzItem(url):
        """Получение базовой информации о товаре с магазина bratz

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """
        #TODO: сделать парсинг preorder'ов

        curl = f'https://www.bratz.com/products/{url.split("products/")[-1]}.js'
        item = StoresApi.getInfo(curl = curl, url = url, priceForFreeShipment = 50, storeName = OrdersConsts.Stores.bratz)
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
        js = soup.find('script', id='__NEXT_DATA__', type='application/json').text
        js = json.loads(js)
        js = js['props']['pageProps']['product']

        item = {}

        item['itemPrice'] = float(js['priceRange']['minVariantPrice']['amount'])
        item['id'] = js['id'].split('/')[-1]
        item['status'] = OrdersConsts.StoreStatus.in_stock if js['availableForSale'] else OrdersConsts.StoreStatus.sold
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = 8.99
        item['page'] = url
        item['mainPhoto'] = js['images']['edges'][0]['node']['transformedSrc']
        item['name'] = js['handle']
        item['siteName'] = OrdersConsts.Stores.makeship

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
                                 shipmentPrice = 20, storeName = OrdersConsts.Stores.plushshop)
        return item