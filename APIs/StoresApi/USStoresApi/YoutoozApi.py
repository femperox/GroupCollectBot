from APIs.webUtils import WebUtils 
from pprint import pprint
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from confings.Consts import ShipmentPriceType as spt, Stores
from APIs.posredApi import PosredApi

class YoutoozApi:

    @staticmethod
    def getShipmentRates():
        """Спарсить стоимости доставок youtooz

        Returns:
            dict: словарь соответсвий стоимости доставок к типам товаров
        """

        soup = WebUtils.getSoup('https://youtooz.com/pages/shipping-policy', )

        table = soup.find('tbody')
        rows = table.findAll("tr", {'data-mce-fragment': '1'})

        shipment_prices = {}
        for row in rows[1:]:
            if row.find('td', {'colspan': '5'}) is not None:
                continue

            item_shipment = row.find('td', {'style': 'text-align: center; height: 22px; width: 211.145px;'}).text
            if item_shipment not in ['INTL', 'US']:
                continue

            if row.find('strong', {'data-mce-fragment': '1'}) is not None:
                item_type = row.find('strong', {'data-mce-fragment': '1'}).text.lower()

            if row.find('td', {'style': 'text-align: center; height: 22px; width: 142.855px;'}) is not None:
                item_size = row.find('td', {'style': 'text-align: center; height: 22px; width: 142.855px;'}).text
            elif row.find('td', {'rowspan' : True}) is not None:
                item_size = row.find('td', {'rowspan' : True}).text
            else:
                continue
            item_size = item_size.replace('\n', '').replace('*', '').lower()



            item_shipment_price = row.find('td', {'style': 'text-align: center; height: 22px; width: 93px;'}).text.lower()
            item_shipment_price = spt.free if item_shipment_price == 'free' else int(item_shipment_price.replace('$', ''))
            
            if item_type in shipment_prices.keys():
                if item_size in shipment_prices[item_type].keys():
                    continue
                shipment_prices[item_type][item_size] = item_shipment_price
            else:
                shipment_prices[item_type] = {item_size: item_shipment_price}

        return shipment_prices
        
    @staticmethod
    def setShipmentPrice(url):
        """Назначить цену доставки для товара

        Args:
            url (string): ссылка на товар

        Returns:
            int | ShipmentPriceType: цена доставки
        """
        shipment_prices = YoutoozApi.getShipmentRates()

        url_lower = url.lower()
        item_type = 'vinyl'

        if url_lower.find('plush') > -1:
            item_type = 'plush'
            if url_lower.find('weighted') > -1:
                return shipment_prices[item_type]['weighted 16"']
            elif url_lower.find('2ft') > -1:
                return shipment_prices[item_type]['2ft']
            elif url_lower.find('plush-bag') > -1:
                return shipment_prices[item_type]['plush bag']
            else:
                return shipment_prices[item_type]['4"/6"/9"/1ft/16"']
        elif url_lower.find('slippers') > -1:
            return shipment_prices['slippers']['slippers']
        elif url_lower.find('jenga') > -1:
            return shipment_prices['jenga']['jenga']
        elif url_lower.find('monopoly') > -1:
            return shipment_prices['monopoly']['monopoly']
        elif url_lower.find('print') > -1:
            return shipment_prices['prints']['prints']
        elif url_lower.find('mug') > -1:
            return shipment_prices['mugs']['mug']
        elif url_lower.find('pin') > -1:
            return shipment_prices['pins']['set']
        elif url_lower.find('gummies') > -1:
            return shipment_prices['gummies']['pack']
        else:
            if url_lower.find('1ft') > -1:
                return shipment_prices[item_type]['1ft']
            else:
                return shipment_prices[item_type]['5"']

    @staticmethod
    def parseYoutoozItem(url):
        """Получение базовой информации о товаре с магазина Youtooz

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """
        soup = WebUtils.getSoup(url)

        js = soup.findAll('script', type='application/ld+json')[0].text.replace('\n','')
        js = json.loads(js)

        item = {}
        item['itemPrice'] = int(js['offers'][0]['price'])
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = YoutoozApi.setShipmentPrice(url = url)
        item['page'] = url
        item['mainPhoto'] = js['image'][0].replace('_small', '')
        item['name'] = js['name']
        item['endTime'] = datetime.now() + relativedelta(years=3)
        item['siteName'] = Stores.youtooz
        item['id'] = js['offers'][0]['sku']

        commission = PosredApi.getСommissionForItemUSD()
        if item['shipmentPrice'] == spt.free:
            format_string = item['itemPrice']
            format_number = item['itemPrice']
        else:
            format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
            format_number = item['itemPrice'] + item['shipmentPrice']
        item['posredCommission'] = commission['posredCommission'].format(format_string)
        item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)

        return item
        