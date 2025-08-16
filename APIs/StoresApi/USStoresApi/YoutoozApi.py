from APIs.webUtils import WebUtils 
from pprint import pprint
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from confings.Consts import OrdersConsts
from APIs.PosredApi.posredApi import PosredApi
from APIs.StoresApi.USStoresApi.StoresApi import StoresApi
import re 

class YoutoozApi:

    @staticmethod
    def getShipmentRates():
        """Спарсить стоимости доставок youtooz

        Returns:
            dict: словарь соответсвий стоимости доставок к типам товаров
        """
        soup = WebUtils.getSoup('https://youtooz.com/pages/shipping-policy', )

        try:
            table = soup.find('div', {'dir': 'ltr'})
            rows = table.findAll("tr")

            shipment_prices = {}
            for row in rows[1:]:
                columns = row.findAll("td")
                if len(columns) == 1:
                    continue
                elif len(columns) == 5:
                    if 'US' not in columns[2].text.strip():
                        continue
                    key_item = columns[0].text.strip().lower()
                    key_item_type = columns[1].text.strip().lower()
                    shipment_price = columns[3].text.strip().replace('$', '')
                elif len(columns) == 3:
                    if 'US' not in columns[1].text.strip():
                        continue
                    key_item_type = columns[0].text.strip().lower()
                    shipment_price = columns[2].text.strip().replace('$', '')

                if key_item not in shipment_prices:
                    shipment_prices[key_item] = {}
                shipment_prices[key_item][key_item_type] = int(shipment_price)

            return shipment_prices
        
        except Exception as e:
            pprint(e)
    

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
            return shipment_prices['prints']['unframed']
        elif url_lower.find('unframed') > -1:
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

        variant = None
        item_id = url.split("products/")[-1]
        if item_id.find('?variant=') > -1:
            curl = f'https://youtooz.com/products/{item_id.split("?variant=")[0]}.js'
            variant = int(item_id.split("?variant=")[1])
        else:
            curl = f'https://youtooz.com/products/{item_id}.js'

        item = StoresApi.getInfo(curl = curl, url = url, storeName = OrdersConsts.Stores.youtooz,
                                 shipmentPrice = YoutoozApi.setShipmentPrice(url = url), variant = variant)

        return item