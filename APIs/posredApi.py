from confings.Consts import CURRENCY_API, CURRENT_POSRED, Stores, CURRENCIES
from APIs.webUtils import WebUtils
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
            if json_item['codeTo'] == 'RUB':
                return float(json_item['rate'])+ 0.07
            

    @staticmethod
    def getСommissionForItem(url):
        """Получить комиссию посреда на товар по ссылке. Логика может меняться в зависимости от текущего посредника. 
           На 19.04.2024 возвращает коммишку в %

        Args:
            url (string): ссылка на тоавр в магазине

        Returns:
            Dict[int, CURRENCIES]: коммишка в % (на 19.04.2024)
        """
        from JpStoresApi.StoreSelector import StoreSelector
        
        commissionFree = [Stores.mercari, Stores.payPay, Stores.yahooAuctions, Stores.amazon]
        standartCommissionPercent = 10

        ss = StoreSelector()
        ss.url = url

        if ss.getStoreName() in commissionFree:
            return {'value': 0, 'key': CURRENCIES.percent}
        else:
            return {'value': standartCommissionPercent, 'key': CURRENCIES.percent}
        
    @staticmethod
    def isPercentCommision(commission):
        """В процентах ли коммишка посреда

        Args:
            commission (Dict[int, CURRENCIES]): коммишка

        Returns:
            boolean: результат проверки
        """

        return commission['key'] == CURRENCIES.percent


        