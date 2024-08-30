from confings.Consts import CURRENCY_API, CURRENT_POSRED, Stores, CURRENCIES, CURRENCY_USD_API, CURRENCY_API_JPY_AMI
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
            if json_item['codeTo'] in CURRENCIES.rub.value:
                return float(json_item['rate'])+ 0.01
            
    @staticmethod
    def getCurrentAmiCurrencyRate():
        """Получить текущий курс рубля по отношению к йене для АмиАми

        Returns:
            float: курс рубля
        """

        soup = WebUtils.getSoup(url = CURRENCY_API_JPY_AMI)
        currencyScript = soup.findAll('script', id='__NEXT_DATA__')[0]
        js = json.loads(currencyScript.text)
        js = js["props"]["pageProps"]["data"]["blocks"][4]["list"]

        for json_item in js:
                        
            if json_item['title'] in CURRENCIES.yen.value:
                return json_item['sale']['value'] + 0.015
            

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
                return json_item['rate'] + 1.5
        

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
        
        #commissionFree = [Stores.mercari, Stores.payPay, Stores.yahooAuctions, Stores.amazon]
        ss = StoreSelector()
        ss.url = url
        if ss.getStoreName() == Stores.amiAmi and ss.isEngAmi(url=url):
            standartCommissionPercent = 0
        else:
            standartCommissionPercent = 6

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


        