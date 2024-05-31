import os
import xmltodict
import requests
import datetime
from Logger import logger
from pprint import pprint
import json
from APIs.webUtils import WebUtils 
from confings.Consts import PREFECTURE_CODE, CURRENT_POSRED
from traceback import print_exc
from APIs.posredApi import PosredApi
from confings.Consts import ShipmentPriceType

def getRep(app_id, id):
    """Получение репутации продавца

    Args:
        app_id (string): айди приложения
        id (string): айди продавца

    Returns:
        list: список: 1ый элемент - хорошая репутация
    """

    curl = f'https://auctions.yahooapis.jp/AuctionWebService/V1/ShowRating?appid={app_id}&id={id}'

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

def getPic(app_id, id):
    """Получение ссылки на изображение лота

    Args:
        app_id (string): айди приложения
        id (string): айди лота
        
    Returns:
        string: ссылка на заглавное изображение лота
    """

    curl = f'https://auctions.yahooapis.jp/AuctionWebService/V2/auctionItem?appid={app_id}&auctionID={id}'

    headers = WebUtils.getHeader()
    page = requests.get(curl, headers=headers)
    xml = xmltodict.parse(page.content)

    return xml['ResultSet']['Result']['Img']['Image1']['#text']

def getShipmentPrice(app_id, id, seller_id , postage_id = 1, item_weight = 0):
    """Получение стоимости доставки по Японии

    Args:
        app_id (string): айди приложения
        id (string): айди лота
        seller_id (string): айди продавца

    Returns:
        string: стоимость доставки по Японии
    """
    pref_code = PREFECTURE_CODE[CURRENT_POSRED]

    if seller_id == '':
        curl = f'https://auctions.yahooapis.jp/v1/public/items/{id}/shipments?pref_code={pref_code}&appid={app_id}'
    else:
        weight = f'&weight={item_weight}' if int(item_weight)>0 else ''
        curl =f'https://auctions.yahooapis.jp/v1/public/shoppinginfo/shipments?&pref_code={pref_code}&appid={app_id}&shopping_seller_id={seller_id}&shopping_item_code={id}&shopping_postage_set={postage_id}&price=100{weight}'
    
    print()
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

def getCurrentPrice(app_id, id):
    """Получение текущей цены аукциона
    
     Args:
        app_id (string): айди приложения
        id (string): айди лота

    Returns:
        string: текущая цена лота со значком йены
    
    """
    
    try:
        curl = f'https://auctions.yahooapis.jp/AuctionWebService/V2/auctionItem?appid={app_id}&auctionID={id}'
        headers = WebUtils.getHeader()
        page = requests.get(curl, headers=headers)
        xml = xmltodict.parse(page.content)

        return float(xml['ResultSet']['Result']['Price'])
    except Exception as e:
        
        pprint(e)
    
    
def getAucInfo(app_id, id):
    """Получение базовой информации о лоте

    Args:
        app_id (string): айди приложения
        id (string): айди лота

    Returns:
        dict: словарь с информацией о лоте
    """

    info = {}
    try:
        curl = f'https://auctions.yahooapis.jp/AuctionWebService/V2/auctionItem?appid={app_id}&auctionID={id}'

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
            
            
            info['shipmentPrice'] = getShipmentPrice(app_id, id, info['ShoppingSellerId'], info['PostageSetId'], info['ItemWeight'])

        info['itemPrice'] = float(xml['ResultSet']['Result']['Price'])
        info['tax'] = float(xml['ResultSet']['Result']['TaxRate'])
        info['itemPriceWTax'] = float(xml['ResultSet']['Result']['TaxinPrice']) if 'itemPriceWTax' in xml['ResultSet']['Result'] else info['itemPrice']
        info['siteName'] = 'yahooAuctions'

        posredCommission = PosredApi.getСommissionForItem(info['page'])
        if PosredApi.isPercentCommision(posredCommission):

            if info['shipmentPrice'] not in [ShipmentPriceType.free, ShipmentPriceType.undefined]:
                info['posredCommission'] = f"({int(info['itemPriceWTax'])} + {int(info['shipmentPrice'])})*{posredCommission['value']/100 if posredCommission['value'] > 0 else 0}"
                info['posredCommissionValue'] = (info['itemPriceWTax'] + info['shipmentPrice'])*(posredCommission['value']/100)
            else:
                info['posredCommission'] = f"{int(info['itemPriceWTax'])}*{posredCommission['value']/100 if posredCommission['value'] > 0 else 0}"
                info['posredCommissionValue'] = info['itemPriceWTax']*(posredCommission['value']/100)
        else:
            info['posredCommission'] = posredCommission['value']

        return info
        
    except Exception as e:
        pprint(e)
        print_exc()
    
