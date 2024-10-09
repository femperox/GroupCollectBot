from APIs.webUtils import WebUtils 
from pprint import pprint
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from confings.Consts import ShipmentPriceType as Stores
from APIs.posredApi import PosredApi

class MakeShipApi:

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
