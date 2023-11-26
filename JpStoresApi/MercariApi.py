from APIs.webUtils import WebUtils 
import requests
from pprint import pprint
import mercari
import json
from SQLS.DB_Operations import GetNotSeenProducts
from random import randint, choice
from confings.Consts import ShipmentPriceType as spt
import uuid
import time


class MercariApi:

    FREE_SHIPPING = 2

    @staticmethod
    def curlMercariApi(curl, uuid_gen_word, method = 'GET'):

        headers = WebUtils.getHeader()
        headers['DPOP'] = mercari.generate_DPOP(uuid=f"{randint(0,100)}{uuid_gen_word}", method=method, url=curl)

        return headers

    @staticmethod
    def monitorMercariCategory(key_word, type_id):

        curl = 'https://api.mercari.jp/v2/entities:search'
        headers = MercariApi.curlMercariApi(curl = curl, uuid_gen_word = key_word, method = "POST")       

        params =  { 
                  "pageSize":50,
                  "searchSessionId": uuid.uuid4().hex,
                  "indexRouting": "INDEX_ROUTING_UNSPECIFIED",
                  "searchCondition":{"keyword":key_word,
                                     "excludeKeyword":"",
                                     "sort":"SORT_CREATED_TIME",
                                     "order":"ORDER_DESC",
                                     "status":["STATUS_ON_SALE"],
                                     },
                "serviceFrom":"suruga",
                "defaultDatasets": [],
				} 
        
        session = requests.session()
        page = session.post(curl, headers=headers, json=params)
        js = page.json() 

        item_list_raw = []
        item = {}
        
        for product in js['items']:

            item['itemPrice'] = product['price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0 # Всегда включена в цену
            item['shipmentPrice'] = spt.free if int(product['shippingPayerId']) == MercariApi.FREE_SHIPPING else spt.undefined
            item['page'] = f'https://jp.mercari.com/item/{product["id"]}'
            item['sellerId'] = product['sellerId']
            item['itemId'] = product["id"]
            item['siteName'] = 'mercari'
            item_list_raw.append(item.copy())

        item_list_ids = GetNotSeenProducts([item['itemId'] for item in item_list_raw], type_id= type_id)
        item_list_raw = [item for item in item_list_raw if item['itemId'] in item_list_ids]
        item_list = []

        proxies = []
        if item_list_raw: 
            proxies = WebUtils.getProxyServerNoSelenium()

        for item in item_list_raw:
            proxy = choice(proxies)
            time.sleep(0.2)
            item['mainPhoto'] = MercariApi.getPic(item["itemId"], proxy = proxy)
            time.sleep(0.2)
            seller = MercariApi.getSelerInfo(seller_id =item['sellerId'], proxy = proxy)
            item['goodRate'] = seller['goodRate']
            item['badRate'] = seller['badRate']
            item['seller']  = seller['seller']

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
        item['itemPrice'] = js['data']['price']
        item['tax'] = 0
        item['itemPriceWTax'] = 0 # Всегда включена в цену
        item['shipmentPrice'] = spt.free if int(js['data']['shipping_payer']['id']) == MercariApi.FREE_SHIPPING else spt.undefined
        item['page'] = url
        item['mainPhoto'] = js['data']['photos'][0]
        item['siteName'] = 'mercari'

        return item