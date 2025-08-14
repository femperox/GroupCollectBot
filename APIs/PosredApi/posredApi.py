from confings.Consts import PosrednikConsts, OrdersConsts
from APIs.webUtils import WebUtils
from APIs.StoresApi.StoreSelectorParent import StoreSelectorParent
from APIs.PosredApi.DaromApi import DaromApi
from APIs.PosredApi.EasyShipApi import EasyShipApi
import requests
import json
from pprint import pprint
import re

class PosredApi:

    @staticmethod
    def pickRightPosredByOrderType(order_type: OrdersConsts.OrderTypes):

        if order_type == OrdersConsts.OrderTypes.jp:
            return DaromApi()
        elif order_type == OrdersConsts.OrderTypes.us:
            return EasyShipApi()

    @staticmethod
    def getPosredOrderByOrderId(order_id, formatted_order_id = ''):

        if PosredApi.getPosredByOrderId(order_id = order_id) == PosrednikConsts.DaromJp:
            return PosrednikConsts.posredUrls[PosrednikConsts.DaromJp].format(formatted_order_id)
        elif PosredApi.getPosredByOrderId(order_id = order_id) == PosrednikConsts.EasyShip:
            return PosrednikConsts.posredUrls[PosrednikConsts.EasyShip]

    @staticmethod
    def getPosredByOrderId(order_id):
        """Получить посреда по id заказа

        Args:
            order_id (string): id заказа

        Returns:
            string: посредник
        """

        if re.fullmatch(r'D-\d+', order_id):
            return PosrednikConsts.DaromJp
        elif re.fullmatch(r's\d{7,10}', order_id):
            return PosrednikConsts.EasyShip
        return ''
    
    @staticmethod
    def getCurrentCurrencyRate():
        """Получить текущий курс рубля по отношению к йене

        Returns:
            float: курс рубля
        """
        headers = WebUtils.getHeader()
        page = requests.get(PosrednikConsts.CURRENCY_API[PosrednikConsts.CURRENT_POSRED], headers=headers)
        js = json.loads(page.text)


        for json_item in js:
            if json_item['codeTo'] in PosrednikConsts.CURRENCIES.rub.value:
                return float(json_item['rate']) 
            
    @staticmethod
    def getCurrentAmiCurrencyRate():
        """Получить текущий курс рубля по отношению к йене для АмиАми

        Returns:
            float: курс рубля
        """

        soup = WebUtils.getSoup(url = PosrednikConsts.CURRENCY_API_JPY_AMI)
        currencyScript = soup.findAll('script')[-1].text.replace('\\', '').replace("self.__next_f.push(", '').replace('n"])', '')
        currencyJPYStart = currencyScript.find('{"title":"JPY"')
        currencyJPYEnd = currencyScript.find(']},{"_template":"infoBgBlock","titleBlock":"Конвертация')
        
        js = json.loads(currencyScript[currencyJPYStart:currencyJPYEnd])

        return js['sale']['value'] + 0.025

    @staticmethod
    def getCurrentUSDCurrencyRate():
        """Получить текущий курс рубля по отношению к доллару

        Returns:
            float: курс рубля
        """

        headers = WebUtils.getHeader()
        page = requests.get(PosrednikConsts.CURRENCY_USD_API, headers=headers)
        js = json.loads(page.text)

        return js['Valute']['USD']['Value'] + 7
    
    @staticmethod
    def getCurrentCurrencyRateByUrl(url):
        from APIs.utils import formShortList
        store_selector = StoreSelectorParent()

        store_selector.url = url
        current_store_name = store_selector.getStoreName()

        jpStores = formShortList(OrdersConsts.Stores.availableStoreJp)
        usStores = formShortList(OrdersConsts.Stores.availableStoreUS)

        if current_store_name in jpStores:
            return PosredApi.getCurrentCurrencyRate()
        elif current_store_name in usStores:
            return PosredApi.getCurrentUSDCurrencyRate()
        else:
            return PosredApi.getCurrentCurrencyRate()     

    @staticmethod
    def getCurrentCurrencyRateByOrderType(order_type):
        """Получить текущий курс в зависимости от типа закупки

        Args:
            order_type (OrderTypes): тип закупки

        Returns:
            float: курс рубля
        """

        if order_type == OrdersConsts.OrderTypes.ami:
            return PosredApi.getCurrentCurrencyRate()
        elif order_type == OrdersConsts.OrderTypes.us:
            return PosredApi.getCurrentUSDCurrencyRate()
        elif order_type == OrdersConsts.OrderTypes.jp:
            return PosredApi.getCurrentCurrencyRate()

    @staticmethod
    def getСommissionForItem(url):
        """Получить комиссию посреда на товар по ссылке. Логика может меняться в зависимости от текущего посредника. 
           На 19.04.2024 возвращает коммишку в %

        Args:
            url (string): ссылка на тоавр в магазине

        Returns:
            Dict[int, CURRENCIES]: коммишка в % (на 19.04.2024)
        """
        from APIs.StoresApi.JpStoresApi.StoreSelector import StoreSelector
        
        ss = StoreSelector()
        ss.url = url
        if ss.getStoreName() == OrdersConsts.Stores.amiAmi and ss.isEngAmi(url=url):
            standartCommissionPercent = 2.2
        else:
            standartCommissionPercent = 6

        def commission(price):
            return price*standartCommissionPercent/100

        return {'key': PosrednikConsts.CURRENCIES.percent,
                'value': standartCommissionPercent,
                'posredCommissionValue': commission, 
                'posredCommission': '{}*'+'{:0.3f}'.format(standartCommissionPercent/100)}
    
    @staticmethod
    def getСommissionForItemUSD():
        """Получить комиссию для товара в USD

        Returns:
            dict: словарь: тип комиссии, форматируемая строка коммишки, функция расчета коммишки
        """

        def commission(price):
            return 1.3 + price*0.02

        return {'key': PosrednikConsts.CURRENCIES.mixed,
                'value': '1.3$ + 2%',
                'posredCommission': '1.3 + {}*0.02',
                'posredCommissionValue': commission}        
    
    @staticmethod
    def getCommissionForCollectOrder(order_type):
        """Получить строку с расчётом коммишки для закупок

        Args:
            order_type (OrderTypes): тип закупки

        Returns:
            string: форматируемая строка с результатом
        """

        if order_type == OrdersConsts.OrderTypes.ami:
            return '{}*0,1'
        elif order_type == OrdersConsts.OrderTypes.us:
            return '{0}*0,1 + {0}*0,02 + 1,3/{1}'
        elif order_type == OrdersConsts.OrderTypes.jp:
            return '{0}*0,1 + {0}*0,038'