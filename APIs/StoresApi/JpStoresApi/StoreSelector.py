from pprint import pprint
from confings.Consts import Stores
from APIs.StoresApi.StoreSelectorParent import StoreSelectorParent
from APIs.StoresApi.JpStoresApi.yahooApi import yahooApi as ya
from APIs.StoresApi.JpStoresApi.SecondaryStoresApi import SecondaryStoreApi as ssa
from APIs.StoresApi.JpStoresApi.StoresApi import StoreApi as sa
from APIs.StoresApi.JpStoresApi.AmiAmiApi import AmiAmiApi
from APIs.StoresApi.JpStoresApi.MercariApi import MercariApi

class StoreSelector(StoreSelectorParent):

    @staticmethod
    def isEngAmi(url):
        return url.find('/eng/') > -1

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
            yahooApi = ya()
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
    
