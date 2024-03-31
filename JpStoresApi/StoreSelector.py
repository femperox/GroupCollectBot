from pprint import pprint
import re
from confings.Consts import RegexType, Stores
from JpStoresApi.yahooApi import getAucInfo
from JpStoresApi.SecondaryStoresApi import SecondaryStoreApi as ssa
from JpStoresApi.StoresApi import StoreApi as sa
from JpStoresApi.AmiAmiApi import AmiAmiApi
from JpStoresApi.MercariApi import MercariApi
import json
from confings.Consts import PRIVATES_PATH

class StoreSelector:

    url = ''

    def getStoreName(self):
        '''
        Возвращает название сайта (его домен)

        :param url: ссылка на товар
        :return:
        '''
        name = re.findall(RegexType.regex_store_url, self.url)[0][2:-1]
        name = name.replace('jp','').replace('com','').replace('www', '').replace('co', '').replace('order.', '').replace('.','')
        return name
    
    def getItemID(self):
        """Получить id товара в магазине

        Returns:
            string: id товара
        """

        id = self.url.split('/')[-1]
        return id
    
    def getStoreUrlByItemId(self, item_id, store_type):
        """Получить ссылку на товар магазина по его id и типу

        Args:
            item_id (string): id товара
            store_type (Stores): тип магазина

        Returns:
            string: ссылка на товар
        """

        if store_type == Stores.mercari:
            return f'https://jp.mercari.com/item/{item_id}'
        elif store_type == Stores.yahooAuctions:
            return f'https://page.auctions.yahoo.co.jp/jp/auction/{item_id}'

    def selectStore(self, url):
        """Определение магазина по заданной ссылке

        Args:
            url (string): ссылка на тоавр в магазине

        Returns:
            dict: информация о товаре по заданной ссылке
        """

        self.url = url
        site = self.getStoreName()
        item = {}

        if site == Stores.mercari:
            item = MercariApi.parseMercariPage(url, self.getItemID())

        elif site == Stores.payPay:
            item = ssa.parsePayPay(url, self.getItemID())

        elif site == Stores.yahooAuctions:
            
            tmp_dict = json.load(open(PRIVATES_PATH, encoding='utf-8'))
            app_id = tmp_dict['yahoo_jp_app_id']
            item = getAucInfo(app_id= app_id,id = self.getItemID())

        elif site == Stores.amiAmi:
            pprint(Stores.amiAmi)
            
            if url.find('/eng/')>0:
                AmiAmiApi.startDriver()
                item = AmiAmiApi.parseAmiAmiEng(url, self.getItemID().split("=")[-1])
                AmiAmiApi.stopDriver()
            else:
                item = ''
                item = AmiAmiApi.parseAmiAmiJp(url)
            
        elif site == Stores.mandarake:
            item = ssa.parseMandarake(url)

        elif site == Stores.animate:
            
            item = sa.parseAnimate(self.getItemID())


        return item
    
