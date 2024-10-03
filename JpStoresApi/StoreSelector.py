from pprint import pprint
import re
from confings.Consts import RegexType, Stores
from JpStoresApi.yahooApi import yahooApi
from JpStoresApi.SecondaryStoresApi import SecondaryStoreApi as ssa
from JpStoresApi.StoresApi import StoreApi as sa
from JpStoresApi.AmiAmiApi import AmiAmiApi
from JpStoresApi.MercariApi import MercariApi

class StoreSelector:

    @staticmethod
    def isEngAmi(url):
        return url.find('/eng/') > -1

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
        id = id.replace('?source_location=share', '').replace('&utm_source=web&utm_medium=share', '').replace('detail.php?product_id=', '')
        id = id.replace('detail?scode=', '').replace('detail?gcode=', '')
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
        item_id = self.getItemID()
        item = {}

        if site == Stores.mercari:

            if url.find('/shops/') > -1:
                item = MercariApi.parseMercariShopsPage(url, item_id.split('?')[0])
            else:
                item = MercariApi.parseMercariPage(url, item_id)

        elif site == Stores.payPay:
            item = ssa.parsePayPay(url, item_id)

        elif site == Stores.yahooAuctions:
            item = yahooApi.getAucInfo(id = item_id)

        elif site == Stores.amiAmi:
            
            if url.find('/eng/')>0:
                AmiAmiApi.startDriver(thread_index=0)
                item = AmiAmiApi.parseAmiAmiEng(url, item_id.split("=")[-1])
                AmiAmiApi.stopDriver(thread_index=0)
            else:
                item = AmiAmiApi.parseAmiAmiJp(url)
            
        elif site == Stores.mandarake:
            item = ssa.parseMandarake(url)

        elif site == Stores.animate:
            
            item = sa.parseAnimate(item_id)

        item['siteName'] = site
        item['id'] = item_id
        
        return item
    
