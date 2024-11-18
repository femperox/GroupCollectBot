from confings.Consts import CURRENCY_API, CURRENT_POSRED, Stores, CURRENCIES, CURRENCY_USD_API, CURRENCY_API_JPY_AMI, OrderTypes
from APIs.webUtils import WebUtils
from APIs.StoresApi.StoreSelectorParent import StoreSelectorParent
import requests
import json
from pprint import pprint


class PosredApi:
    
    @staticmethod
    def getCurrentCurrencyRate():
        """Получить текущий курс рубля по отношению к йене

        Returns:
            float: курс рубля
        """
        headers = WebUtils.getHeader()
        page = requests.get(CURRENCY_API[CURRENT_POSRED], headers=headers)
        js = json.loads(page.text)


        for json_item in js:
            if json_item['codeTo'] in CURRENCIES.rub.value:
                return float(json_item['rate']) #- 0.01
            
    @staticmethod
    def getCurrentAmiCurrencyRate():
        """Получить текущий курс рубля по отношению к йене для АмиАми

        Returns:
            float: курс рубля
        """

        soup = WebUtils.getSoup(url = CURRENCY_API_JPY_AMI)
        currencyScript = soup.findAll('script')[-1].text.replace('\\', '').replace("self.__next_f.push(", '').replace('n"])', '')
        currencyJPYStart = currencyScript.find('{"title":"JPY"')
        currencyJPYEnd = currencyScript.find(']},{"_template":"infoBgBlock","titleBlock":"Конвертация')
        
        js = json.loads(currencyScript[currencyJPYStart:currencyJPYEnd])

        return js['sale']['value'] + 0.015

    @staticmethod
    def getCurrentUSDCurrencyRate():
        """Получить текущий курс рубля по отношению к доллару

        Returns:
            float: курс рубля
        """

        headers = WebUtils.getHeader()
        page = requests.get(CURRENCY_USD_API, headers=headers)
        js = json.loads(page.text)
        
        for json_item in js['result']:
            if json_item['from'] == '643' and json_item['to'] == '840':
                return json_item['rate'] + 9.66
    
    @staticmethod
    def getCurrentCurrencyRateByUrl(url):
        from APIs.utils import formShortList
        store_selector = StoreSelectorParent()

        store_selector.url = url
        current_store_name = store_selector.getStoreName()

        jpStores = formShortList(Stores.availableStoreJp)
        usStores = formShortList(Stores.availableStoreUS)

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

        if order_type == OrderTypes.ami:
            return PosredApi.getCurrentAmiCurrencyRate()
        elif order_type == OrderTypes.us:
            return PosredApi.getCurrentUSDCurrencyRate()
        elif order_type == OrderTypes.jp:
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
        if ss.getStoreName() == Stores.amiAmi and ss.isEngAmi(url=url):
            standartCommissionPercent = 0
        else:
            standartCommissionPercent = 6

        def commission(price):
            return price*standartCommissionPercent/100

        return {'key': CURRENCIES.percent,
                'value': standartCommissionPercent,
                'posredCommissionValue': commission, 
                'posredCommission': '{}*'+f'{standartCommissionPercent/100}',}
    
    @staticmethod
    def getСommissionForItemUSD():
        """Получить комиссию для товара в USD

        Returns:
            dict: словарь: тип комиссии, форматируемая строка коммишки, функция расчета коммишки
        """

        def commission(price):
            return 1.3 + price*0.02

        return {'key': CURRENCIES.mixed,
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

        if order_type == OrderTypes.ami:
            return '{}*0,1'
        elif order_type == OrderTypes.us:
            return '{0}*0,1 + {0}*0,02 + 1,3/{1}'
        elif order_type == OrderTypes.jp:
            return '{0}*0,1 + {0}*0,038'