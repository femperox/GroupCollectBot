from pprint import pprint
from confings.Consts import Stores
from APIs.StoresApi.StoreSelectorParent import StoreSelectorParent
from APIs.StoresApi.JpStoresApi.yahooApi import yahooApi as ya
from APIs.StoresApi.JpStoresApi.SecondaryStoresApi import SecondaryStoreApi as ssa
from APIs.StoresApi.JpStoresApi.StoresApi import StoreApi as sa
from APIs.StoresApi.JpStoresApi.AmiAmiApi import AmiAmiApi
from APIs.StoresApi.JpStoresApi.MercariApi import MercariApi
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

    def selectStore(self, url, isLiteCalculate = False):
        """Определение магазина по заданной ссылке

        Args:
            url (string): ссылка на тоавр в магазине

        Returns:
            dict: информация о товаре по заданной ссылке
        """
        yahooApi = ya()

        self.url = url
        site = self.getStoreName()
        item_id = self.getItemID()
        item = {}

        if isLiteCalculate:
            item['siteName'] = site
            item['id'] = item_id
            item['page'] = url

            if site in [Stores.yahooAuctions, Stores.yahooAuctionsShort]:
                item['endTime'] = yahooApi.getEndTime(item_id)
            else:
                item['endTime'] = datetime.now() + relativedelta(years=3)

            return item

        if site == Stores.mercari:
            if url.find('/shops/') > -1:
                item = MercariApi.parseMercariShopsPage(url, item_id.split('?')[0])
            else:
                item = MercariApi.parseMercariPage(url, item_id)
        elif site == Stores.payPay:
            item = ssa.parsePayPay(url, item_id)
        elif site in [Stores.yahooAuctions, Stores.yahooAuctionsShort]:  
            item = yahooApi.getAucInfo(id = item_id)
        elif site == Stores.amiAmi:
            if url.find('/eng/')>0:
                AmiAmiApi.startDriver(3)
                item = AmiAmiApi.parseAmiAmiEng(url, item_id, thread_index = 3)
                AmiAmiApi.stopDriver(3)
            else:
                item = AmiAmiApi.parseAmiAmiJp(url, item_id)  
        elif site == Stores.mandarake:
            item = ssa.parseMandarake(url, item_id)
        elif site == Stores.animate:
            item = sa.parseAnimate(item_id)
        elif site == Stores.suruga:
            item = ssa.parseSuruga(url = url)
        
        return item
    
