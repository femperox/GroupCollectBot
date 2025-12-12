from APIs.webUtils import WebUtils 
from pprint import pprint
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from confings.Consts import OrdersConsts, PosrednikConsts
from APIs.PosredApi.posredApi import PosredApi
from _utils.dateUtils import DateUtils
import requests
import re
from random import choice
import time

class StoresApi:

    @staticmethod
    def setItemStatus(item_available, tags = []):
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
    def getInfoOembed(curl, url, storeName, variant = None, priceForFreeShipment = None, shipmentPrice = None):
        """Получить инфо из oembed запроса по шаблону

        Args:
            curl (string): ссылка на oembed-скрипт
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
                variant_item = [x for x in js['offers'] if x['offer_id'] == variant][0]
                item['itemPrice'] = variant_item['price']
                if 'featured_image' in variant_item:
                    item['mainPhoto'] = variant_item['featured_image']['src']
                else:
                    item['mainPhoto'] = 'https:' + js['thumbnail_url']
                item['name'] = variant_item['title']
                item['status'] = StoresApi.setItemStatus(item_available = variant_item['in_stock'])

            else:
                if len(js['offers']) > 1:
                    item['itemPrice'] = js['offers'][-1]['price']
                else:
                    item['itemPrice'] = js['price']
                item['mainPhoto'] = 'https:' +  js['thumbnail_url']
                item['name'] = js['title']
                item['status'] = StoresApi.setItemStatus(item_available = js['in_stock'])
            
            item['id'] = js['product_id']

            item['tax'] = 0
            item['itemPriceWTax'] = 0
            if priceForFreeShipment is None:
                item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined if shipmentPrice is None else shipmentPrice
            else:
                item['priceForFreeShipment'] = priceForFreeShipment
                item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined if shipmentPrice is None else shipmentPrice
                item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if item['itemPrice'] >= item['priceForFreeShipment'] else item['shipmentPrice']
                        
            item['page'] = url
            item['siteName'] = storeName

            commission = PosredApi.getСommissionForItemUSD()
            if item['shipmentPrice'] in [OrdersConsts.ShipmentPriceType.free, OrdersConsts.ShipmentPriceType.undefined]:
                format_string = item['itemPrice']
                format_number = item['itemPrice']
            else:
                format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
                format_number = item['itemPrice'] + item['shipmentPrice']
            item['posredCommission'] = commission['posredCommission'].format(format_string)
            item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)

        except Exception as e:
            pprint(e)
        finally:
            return item

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
        page = requests.get(curl, headers=headers, verify = False)
        js = page.json()
        item = {}
        try:
            if variant:
                variant_item = [x for x in js['variants'] if x['id'] == variant][0]
                item['itemPrice'] = variant_item['price']
                if 'featured_image' in variant_item and variant_item['featured_image']:
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
            item['siteName'] = storeName

            commission = PosredApi.getСommissionForItemUSD()
            if item['shipmentPrice'] in [OrdersConsts.ShipmentPriceType.free, OrdersConsts.ShipmentPriceType.undefined]:
                format_string = item['itemPrice']
                format_number = item['itemPrice']
            else:
                format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
                format_number = item['itemPrice'] + item['shipmentPrice']
            item['posredCommission'] = commission['posredCommission'].format(format_string)
            item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)

        except Exception as e:
            print(e)
        finally:
            return item

    @staticmethod
    def getInfoVer2(curl, url, storeName, variant = None, priceForFreeShipment = None, shipmentPrice = None):
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
                variant_item = [x for x in js['options'] if x['id'] == variant][0]
                item['itemPrice'] = variant_item['price']
                if 'featured_image' in variant_item and variant_item['featured_image']:
                    item['mainPhoto'] = variant_item['featured_image']['src']
                else:
                    item['mainPhoto'] = js['images'][0]['url']
                item['name'] = variant_item['name']

                item['status'] = StoresApi.setItemStatus(item_available = not variant_item['sold_out'])

            else:
                if len(js['options']) > 1 and js['options'][0]['sold_out'] == True:
                    item['itemPrice'] = js['options'][-1]['price']
                else:
                    item['itemPrice'] = js['price']
                item['mainPhoto'] = js['images'][0]['url']
                item['name'] = js['name']

                item['status'] = StoresApi.setItemStatus(item_available = js['status'] == 'active')
            
            item['itemPrice'] = float(item['itemPrice'])
            item['id'] = js['id']

            item['tax'] = 0
            item['itemPriceWTax'] = 0
            

            if shipmentPrice is None:
                if 'shipping' in js and js['shipping']:
                    item['shipmentPrice'] = [item for item in js['shipping'] if ('country' in item.keys() and item['country']['code'].lower() == 'us')][0]['amount_alone']
                else:
                    item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
            else:
                item['shipmentPrice'] = shipmentPrice
            if priceForFreeShipment is not None:
                item['priceForFreeShipment'] = priceForFreeShipment
                item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if item['itemPrice'] >= item['priceForFreeShipment'] else item['shipmentPrice']
                    
            item['page'] = url
            item['siteName'] = storeName

            commission = PosredApi.getСommissionForItemUSD()
            if item['shipmentPrice'] in [OrdersConsts.ShipmentPriceType.free, OrdersConsts.ShipmentPriceType.undefined]:
                format_string = item['itemPrice']
                format_number = item['itemPrice']
            else:
                format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
                format_number = item['itemPrice'] + item['shipmentPrice']
            item['posredCommission'] = commission['posredCommission'].format(format_string)
            item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)

        except Exception as e:
            print(e)
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
    def parsePlushWonderlandItem(url):
        """Получение базовой информации о товаре с магазина plushwonderland

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """

        variant = None
        item_id = url.split("products/")[-1]
        if item_id.find('?variant=') > -1:
            curl = f'https://plushwonderland.com/products/{item_id.split("?variant=")[0]}.js'
            variant = int(item_id.split("?variant=")[1])
        else:
            curl = f'https://plushwonderland.com/products/{item_id}.js'
        item = StoresApi.getInfo(curl = curl, variant = variant, url = url, storeName = OrdersConsts.Stores.plushwonderland)
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
        item['page'] = url
        item['mainPhoto'] = js['images']['edges'][0]['node']['transformedSrc']
        item['name'] = js['handle']
        item['siteName'] = OrdersConsts.Stores.makeship

        if 'doughboi' in item['name'] or 'hoodie' in item['name']:
            item['shipmentPrice'] = 14.99
        elif 'figure' in item['name']:
            item['shipmentPrice'] = 5.99
        elif ('keychain' in item['name'] or 'cap' in item['name'] or 'p-chain' in item['name']) and not '-plushie' in item['name']:
            item['shipmentPrice'] = 6.99
        elif 'sweatpants' in item['name']:
            item['shipmentPrice'] = 10.99
        elif 'jumbo' in item['name']:
            item['shipmentPrice'] = 9.99
        elif 'socks' in item['name'] or 'pins' in item['name']:
            item['shipmentPrice'] = 4.99
        else:
            item['shipmentPrice'] = 8.99

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
    
    @staticmethod
    def parseJsonRandomStoreItem(url, storeName):
        """Получение базовой информации о товаре с рандомного магазина, что позволит содрать инфо с помощью getInfo

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """

        item = {}
        if url.find('/product') > -1:
            product_string = 'products' if url.find('/products') > -1 else 'product'
            variant = None
            address = url.split(f"/{product_string}")[0]
            item_id = url.split(f"{product_string}/")[-1]
            
            if item_id.find('?variant=') > -1:
                curl = f'{address}/{product_string}/{item_id.split("?variant=")[0]}.js'
                variant = int(item_id.split("?variant=")[1])
            else:
                curl = f'{address}/{product_string}/{item_id}.js'
            try:
                params = {
                    'curl': curl,
                    'variant': variant,
                    'url': url,
                    'storeName': storeName
                }
                item = StoresApi.getInfo(**params) if product_string == 'products' else StoresApi.getInfoVer2(**params)
            except Exception as e:
                print(e)
                return item
        return item
    
    def parseHotTopicItem(url):
        """Получение базовой информации о товаре с магазина hottopic

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """

        httpxClient = WebUtils.getHttpxClient(isPrivateProxy=True, isExtendedHeader=True) 
        page = httpxClient.get(url)
        item = {}
        try:
            soup = WebUtils.getSoup(rawText = page.text)
            js = soup.find('script', type='application/ld+json').text
            js = json.loads(js)[0]

            if 'hasVariant' in js:
                first_avail = None
                for variant in js['hasVariant']:
                    if 'OnlineOnly' in variant['offers']['availability']:
                        first_avail = variant
                        break
                item['itemPrice'] = float(first_avail['offers']['price'])
                item['mainPhoto'] = first_avail['image']
                item['status'] = OrdersConsts.StoreStatus.in_stock if 'OnlineOnly' in first_avail['offers']['availability'] else OrdersConsts.StoreStatus.sold 
                item['id'] = first_avail['sku']
            else:
                item['itemPrice'] = float(js['offers']['price'])
                item['mainPhoto'] = js['image'][0]
                item['status'] = OrdersConsts.StoreStatus.in_stock if 'OnlineOnly' in js['offers']['availability'] else OrdersConsts.StoreStatus.sold 
                item['id'] = js['sku']
            item['page'] = js['@id']
            item['name'] = js['name']

            item['priceForFreeShipment'] = 75
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if item['itemPrice'] >= item['priceForFreeShipment'] else 7.99
            item['siteName'] = OrdersConsts.Stores.hottopic

            commission = PosredApi.getСommissionForItemUSD()
            if item['shipmentPrice'] in [OrdersConsts.ShipmentPriceType.free, OrdersConsts.ShipmentPriceType.undefined]:
                format_string = item['itemPrice']
                format_number = item['itemPrice']
            else:
                format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
                format_number = item['itemPrice'] + item['shipmentPrice']
            item['posredCommission'] = commission['posredCommission'].format(format_string)
            item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)

        except Exception as e:
            pprint(e)
        finally:
            httpxClient.close()
            return item
        
    def parseTargetItem(item_id):
        """Получение базовой информации о товаре с магазина target

        Args:
            item_id (string): id товара

        Returns:
            dict: словарь с информацией о товаре
        """

        shipping_curl = 'https://redsky.target.com/redsky_aggregations/v1/web/product_fulfillment_and_variation_hierarchy_v1'
        product_curl = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1'
        
        variant = None
        item_id_cleaned = item_id.split('#')[0].split('A-')[-1]
        if '?preselect=' in item_id_cleaned:
            item_id_cleaned, variant = item_id_cleaned.split('?preselect=')

        payload = {
            'is_bot': 'false',
            'tcin': item_id_cleaned,
            'key': '9f36aeafbe60771e321a7cc95a78140772ab3e96',
            'pricing_store_id': 61
        }

        shipping_payload = payload.copy()
        shipping_payload['zip'] = PosrednikConsts.USA_DELIVERY_INDEX
        shipping_payload['state'] = PosrednikConsts.USA_DELIVERY_STATE    
        httpxClient = WebUtils.getHttpxClient(isPrivateProxy=True, isExtendedHeader=True) 

        item = {}
        try:
            time.sleep(1)
            shipment_page = httpxClient.get(url = shipping_curl, params = payload)
            shipment_js = shipment_page.json()
            if not shipment_js:
                return item
            
            shipment_js = shipment_js['data']['product']
            if 'children' in shipment_js:
                if variant is None:
                    variant = [shipment_item['tcin'] for shipment_item in shipment_js['children'] if shipment_item['fulfillment']['shipping_options']['availability_status'] != 'OUT_OF_STOCK'][0]
                    if not variant:
                        return item
                shipment_js = [shipment_item for shipment_item in shipment_js['children'] if variant == shipment_item['tcin']][0]
            
            if shipment_js['fulfillment']['shipping_options']['availability_status'] in ['PRE_ORDER_UNSELLABLE', 'OUT_OF_STOCK']:
                return item
            
            page = httpxClient.get(url = product_curl, params = payload)
            js = page.json()
            if not js:
                return item
            js = js['data']['product']
            if 'children' in js:
                js = [js_item for js_item in js['children'] if variant == js_item['tcin']][0]
            item['itemPrice'] = js['price']['current_retail']
            item['id'] = js['tcin']
            item['name'] = js['item']['product_description']['title']
            item['mainPhoto'] = js['item']['enrichment']['image_info']['primary_image']['url'] +'?wid=600'
            item['page'] = js['item']['enrichment']['buy_url']
            
            item['status'] = OrdersConsts.StoreStatus.pre_order if shipment_js['fulfillment']['shipping_options']['availability_status'] == 'PRE_ORDER_SELLABLE' else OrdersConsts.StoreStatus.in_stock

            item['priceForFreeShipment'] = 35
            item['shipmentPrice'] = shipment_js['pay_per_order_charges']['scheduled_delivery'] if shipment_js['pay_per_order_charges'] else OrdersConsts.ShipmentPriceType.undefined
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if item['itemPrice'] >= item['priceForFreeShipment'] else item['shipmentPrice']

            commission = PosredApi.getСommissionForItemUSD()
            if item['shipmentPrice'] in [OrdersConsts.ShipmentPriceType.free, OrdersConsts.ShipmentPriceType.undefined]:
                format_string = item['itemPrice']
                format_number = item['itemPrice']
            else:
                format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
                format_number = item['itemPrice'] + item['shipmentPrice']
            item['posredCommission'] = commission['posredCommission'].format(format_string)
            item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)
            item['siteName'] = OrdersConsts.Stores.target
        except Exception as e:
            pprint(e)
        finally:
            httpxClient.close()
            return item       



