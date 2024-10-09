import xmltodict
import requests
import datetime
from pprint import pprint
import json
from APIs.webUtils import WebUtils 
from confings.Consts import PREFECTURE_CODE, CURRENT_POSRED, PRIVATES_PATH
from traceback import print_exc
from APIs.posredApi import PosredApi
from confings.Consts import ShipmentPriceType
from confings.Consts import Stores

class yahooApi:

    def __init__(self):

        self.app_id = json.load(open(PRIVATES_PATH, encoding='utf-8'))['yahoo_jp_app_id']

    def getRep(self, id):
        """Получение репутации продавца

        Args:
            id (string): айди продавца

        Returns:
            list: список: 1ый элемент - хорошая репутация
        """

        curl = f'https://auctions.yahooapis.jp/AuctionWebService/V1/ShowRating?appid={self.app_id}&id={id}'

        headers = WebUtils.getHeader()
        page = requests.get(curl, headers=headers)
        xml = xmltodict.parse(page.content)

        try:
            goodRate = xml['ResultSet']['TotalGoodRating']
            badRate = xml['ResultSet']['TotalBadRating']
        except:
            goodRate = 0
            badRate = 0

        return [goodRate, badRate]

    def getPic(self, id):
        """Получение ссылки на изображение лота

        Args:
            id (string): айди лота
            
        Returns:
            string: ссылка на заглавное изображение лота
        """

        curl = f'https://auctions.yahooapis.jp/AuctionWebService/V2/auctionItem?appid={self.app_id}&auctionID={id}'

        headers = WebUtils.getHeader()
        page = requests.get(curl, headers=headers)
        xml = xmltodict.parse(page.content)

        return xml['ResultSet']['Result']['Img']['Image1']['#text']


    def getShipmentPrice(self, id, seller_id , postage_id = 1, item_weight = 0):
        """Получение стоимости доставки по Японии

        Args:
            id (string): айди лота
            seller_id (string): айди продавца

        Returns:
            string: стоимость доставки по Японии
        """
        pref_code = PREFECTURE_CODE[CURRENT_POSRED]

        if seller_id == '':
            curl = f'https://auctions.yahooapis.jp/v1/public/items/{id}/shipments?pref_code={pref_code}&appid={self.app_id}'
        else:
            weight = f'&weight={item_weight}' if int(item_weight)>0 else ''
            curl =f'https://auctions.yahooapis.jp/v1/public/shoppinginfo/shipments?&pref_code={pref_code}&appid={self.app_id}&shopping_seller_id={seller_id}&shopping_item_code={id}&shopping_postage_set={postage_id}&price=100{weight}'
        
        headers = WebUtils.getHeader()
        page = requests.get(curl, headers=headers)
        
        js = json.loads(page.text)

        prices = []
        for method in js['methods']:
            if method['shipping_price'][0]['price']!=None:
                prices.append(method['shipping_price'][0]['price'])
        
        if len(prices):
            return float(min(prices))
        else:
            return ShipmentPriceType.undefined

    def getCurrentPrice(self, id):
        """Получение текущей цены аукциона
        
        Args:
            id (string): айди лота

        Returns:
            string: текущая цена лота со значком йены
        
        """
        
        try:
            curl = f'https://auctions.yahooapis.jp/AuctionWebService/V2/auctionItem?appid={self.app_id}&auctionID={id}'
            headers = WebUtils.getHeader()
            page = requests.get(curl, headers=headers)
            xml = xmltodict.parse(page.content)

            return float(xml['ResultSet']['Result']['Price'])
        except Exception as e:
            
            pprint(e)

    def getEndTime(self, id):
        """Получение даты окончания лота
        
        Args:
            id (string): айди лота

        Returns:
            date: дата окончания лота
        """
        try:
            curl = f'https://auctions.yahooapis.jp/AuctionWebService/V2/auctionItem?appid={self.app_id}&auctionID={id}'

            headers = WebUtils.getHeader()
            page = requests.get(curl, headers=headers)
            xml = xmltodict.parse(page.content)
        
            endTime = xml['ResultSet']['Result']['EndTime'].split('+')[0].replace('T', ' ')
            endTime = datetime.datetime.strptime(endTime, '%Y-%m-%d %H:%M:%S') - datetime.timedelta(hours=6)

            return endTime
        
        except Exception as e:
            pprint(e)
            print_exc()
            return None

    def getAucInfo(self, id):
        """Получение базовой информации о лоте

        Args:
            id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        info = {}
        try:
            curl = f'https://auctions.yahooapis.jp/AuctionWebService/V2/auctionItem?appid={self.app_id}&auctionID={id}'

            headers = WebUtils.getHeader()
            page = requests.get(curl, headers=headers)
            xml = xmltodict.parse(page.content)
        
            info['page'] = xml['ResultSet']['Result']['AuctionItemUrl']
            info['page'] = xml['ResultSet']['Result']['AuctionItemUrl']
            
            info['endTime'] = xml['ResultSet']['Result']['EndTime'].split('+')[0].replace('T', ' ')
            info['endTime'] = datetime.datetime.strptime(info['endTime'], '%Y-%m-%d %H:%M:%S') - datetime.timedelta(hours=6)
            try: 
                info['mainPhoto'] = xml['ResultSet']['Result']['Img']['Image1']['#text']
            except:
                info['mainPhoto'] = ''
                
            try:
                info['goodRate'] = xml['ResultSet']['Result']['Seller']['Rating']['TotalGoodRating']
            except:
                info['goodRate'] = 0
        
            try:
                info['badRate'] = xml['ResultSet']['Result']['Seller']['Rating']['TotalBadRating']
            except:
                info['badRate'] = 0
                
            try:
                info['blitz'] = xml['ResultSet']['Result']['Bidorbuy']
            except:
                info['blitz'] = -1
            
            if 'FreeshippingIcon' in xml['ResultSet']['Result']['Option'].keys():
                info['shipmentPrice'] = ShipmentPriceType.free
            else:
                try: 
                    info['ShoppingSellerId'] = xml['ResultSet']['Result']['Seller']['ShoppingSellerId']
                    info['PostageSetId'] = xml['ResultSet']['Result']['ShoppingItem']['PostageSetId']
                    info['ItemWeight'] = xml['ResultSet']['Result']['ShoppingItem']['ItemWeight']
                except:
                    info['ShoppingSellerId'] = ''
                    info['PostageSetId'] = 1
                    info['ItemWeight'] = 0
                
                
                info['shipmentPrice'] = self.getShipmentPrice(id, info['ShoppingSellerId'], info['PostageSetId'], info['ItemWeight'])

            info['itemPrice'] = float(xml['ResultSet']['Result']['Price'])
            info['tax'] = float(xml['ResultSet']['Result']['TaxRate'])
            info['itemPriceWTax'] = float(xml['ResultSet']['Result']['TaxinPrice']) if 'itemPriceWTax' in xml['ResultSet']['Result'] else info['itemPrice']


            commission = PosredApi.getСommissionForItem(info['page'])
            if info['shipmentPrice'] in [ShipmentPriceType.free, ShipmentPriceType.undefined]:
                format_string = info['itemPrice']
                format_number = info['itemPrice']
            else:
                format_string = f"( {info['itemPrice']} + {info['shipmentPrice']} )"
                format_number = info['itemPrice'] + info['shipmentPrice']
            info['posredCommission'] = commission['posredCommission'].format(format_string)
            info['posredCommissionValue'] = commission['posredCommissionValue'](format_number)  

            info['siteName'] = Stores.yahooAuctions
            info['id'] = id   

            return info
            
        except Exception as e:
            pprint(e)
            print_exc()
    
