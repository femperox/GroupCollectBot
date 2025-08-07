from APIs.webUtils import WebUtils 
import requests
from pprint import pprint
import mercari
from SQLS.DB_Operations import GetNotSeenProducts
from random import randint, choice
from confings.Consts import OrdersConsts
import uuid
from datetime import datetime
from dateutil.relativedelta import relativedelta
from SQLS.DB_Operations import IsExistBannedSeller
from APIs.posredApi import PosredApi


class MercariApi:

    class MercariItemStatus:

        on_sale = 'on_sale'
        trading = 'trading'
        sold = 'sold_out'
        deleted = 'deleted'

    FREE_SHIPPING = 2
    FREE_SHIPPING_SHOPS = 1

    @staticmethod
    def curlMercariApi(curl, uuid_gen_word, method = 'GET'):

        headers = WebUtils.getHeader()
        headers['DPOP'] = mercari.generate_DPOP(uuid=f"{randint(0,100)}{uuid_gen_word}", method=method, url=curl)

        return headers
    
    @staticmethod
    def getAdditionalInfo(item_id, sellerId):
    
        item_info = {}
        proxies = WebUtils.getProxyServer()

        # пока не получим норм результат
        for i in range(5):
            try:
                proxy = choice(proxies)
                item_info['mainPhoto'] = MercariApi.getPic(item_id, proxy = proxy)
                seller = MercariApi.getSelerInfo(seller_id =sellerId, proxy = proxy)
                item_info['goodRate'] = seller['goodRate']
                item_info['badRate'] = seller['badRate']
                item_info['seller']  = f"{seller['seller']} (#{sellerId})"

                return item_info
            
            except Exception as e:
                pprint(e)
                continue

        return 0

    @staticmethod
    def monitorMercariCategory(key_word, type_id):

        curl = 'https://api.mercari.jp/v2/entities:search'
        headers = MercariApi.curlMercariApi(curl = curl, uuid_gen_word = key_word, method = "POST")       

        params =  { 
                  "pageSize":50,
                  "searchSessionId": uuid.uuid4().hex,
                  "indexRouting": "INDEX_ROUTING_UNSPECIFIED",
                  "searchCondition":{
                                     "excludeKeyword":"",
                                     "sort":"SORT_CREATED_TIME",
                                     "order":"ORDER_DESC",
                                     "status":["STATUS_ON_SALE"],
                                     },
                "serviceFrom":"suruga",
                "defaultDatasets": [],
				} 
        
        if key_word.isnumeric():
            params["searchCondition"]["categoryId"] = [int(key_word)]
        else:
            params["searchCondition"]["keyword"] = key_word
        
        session = requests.session()
        page = session.post(curl, headers=headers, json=params)
        js = page.json() 

        item_list_raw = []
        item = {}
        
        for product in js['items']:

            if IsExistBannedSeller(seller_id = product['sellerId'], category = type_id, store_id= OrdersConsts.Stores.mercari):
                    continue            

            item['itemPrice'] = product['price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0 # Всегда включена в цену
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if int(product['shippingPayerId']) == MercariApi.FREE_SHIPPING else OrdersConsts.ShipmentPriceType.undefined
            item['page'] = f'https://jp.mercari.com/item/{product["id"]}'
            item['sellerId'] = product['sellerId']
            item['id'] = product["id"]
            item_list_raw.append(item.copy())

        item_list_ids = GetNotSeenProducts([item['id'] for item in item_list_raw], type_id= type_id)
        item_list_raw = [item for item in item_list_raw if item['id'] in item_list_ids]
        item_list = []

        for item in item_list_raw:

            additionalInfo = MercariApi.getAdditionalInfo(item["id"], item["sellerId"])
            if not additionalInfo:
                continue
            item['mainPhoto'] = additionalInfo['mainPhoto']
            item['goodRate'] = additionalInfo['goodRate']
            item['badRate'] = additionalInfo['badRate']
            item['seller']  = additionalInfo['seller']

            item_list.append(item.copy())
        
        return item_list
    
    def getSelerInfo(seller_id, proxy = ''):

        curl = f'https://api.mercari.jp/users/get_profile?user_id={seller_id}&_user_format=profile'
        headers = MercariApi.curlMercariApi(curl = curl, uuid_gen_word = seller_id)  

        session = requests.session()
        page = session.get(curl, headers=headers, proxies = {'http': f'http://{proxy}'} if proxy else None)
        js = page.json() 

        info = { 'seller': js['data']['name'].replace(' ',''),
                 'goodRate': js['data']['ratings']['good'],
                 'badRate': js['data']['ratings']['bad']
               }

        return info
    
    @staticmethod
    def getPic(item_id, proxy = ''):

        session = requests.session()
        curl = f'https://api.mercari.jp/items/get?id={item_id}'

        headers = MercariApi.curlMercariApi(curl = curl, uuid_gen_word = item_id)    

        page = session.get(curl, headers=headers, proxies = {'http': f'http://{proxy}'} if proxy else None)
        js = page.json() 

        return js['data']['photos'][0]


    @staticmethod
    def parseMercariShopsPage(url, item_id):
        """Получение базовой информации о лоте со вторички mercari.shops

        Args:
            url (string): ссылка на лот
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """
        
        curl = f'https://api.mercari.jp/v1/marketplaces/shops/products/{item_id}?view=FULL&imageType=JPEG'

        headers = MercariApi.curlMercariApi(curl = curl, uuid_gen_word = item_id)  

        session = requests.session()
        page = session.get(curl, headers=headers)
        js = page.json() 

        item = {}
        if 'code' not in js.keys():
            item['itemPrice'] = js['productDetail']['timeSaleDetails']['price'] if js['productDetail']['timeSaleDetails'] else js['price']
            item['itemPrice'] = int(item['itemPrice'])

            item['tax'] = 0
            item['itemPriceWTax'] = 0 # Всегда включена в цену
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if int(js['productDetail']['shippingPayer']['shippingPayerId']) == MercariApi.FREE_SHIPPING_SHOPS else OrdersConsts.ShipmentPriceType.undefined
            item['page'] = url
            item['mainPhoto'] = js['productDetail']['photos'][0]
            item['itemStatus'] = MercariApi.MercariItemStatus.sold if len(js["productTags"]) else MercariApi.MercariItemStatus.on_sale 
            item['endTime'] = datetime.now() + relativedelta(years=3)
            
            commission = PosredApi.getСommissionForItem(item['page'])
            item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
            item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice'])

            item['siteName'] = OrdersConsts.Stores.mercari
            item['id'] = item_id     

        elif js['code'] == 5:
            item['itemStatus'] = MercariApi.MercariItemStatus.deleted   
        return item

        
    @staticmethod
    def parseMercariPage(url, item_id):
        """Получение базовой информации о лоте со вторички mercari

        Args:
            url (string): ссылка на лот
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        session = requests.session()
        curl = f'https://api.mercari.jp/items/get?id={item_id}'

        headers = MercariApi.curlMercariApi(curl = curl, uuid_gen_word = item_id)   
        page = session.get(curl, headers=headers)
        js = page.json() 

        item = {}

        if js['result'] == "OK":
            item['itemPrice'] = js['data']['price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0 # Всегда включена в цену
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if int(js['data']['shipping_payer']['id']) == MercariApi.FREE_SHIPPING else OrdersConsts.ShipmentPriceType.undefined
            item['page'] = url
            item['mainPhoto'] = js['data']['photos'][0]
            item['itemStatus'] = js['data']['status']
            item['endTime'] = datetime.now() + relativedelta(years=3)
            
            commission = PosredApi.getСommissionForItem(item['page'])
            item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
            item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice'])  

            item['siteName'] = OrdersConsts.Stores.mercari
            item['id'] = item_id      

        elif js['result'] == "error":
            item['itemStatus'] = MercariApi.MercariItemStatus.deleted
            
        return item