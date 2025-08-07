from pprint import pprint
from confings.Consts import OrdersConsts
from APIs.StoresApi.StoreSelectorParent import StoreSelectorParent
from APIs.StoresApi.USStoresApi.StoresApi import StoresApi
from APIs.StoresApi.USStoresApi.YoutoozApi import YoutoozApi
from APIs.StoresApi.USStoresApi.AmazonApi import AmazonApi
from datetime import datetime
from dateutil.relativedelta import relativedelta
from APIs.StoresApi.ProductInfoClass import ProductInfoClass

class StoreSelector(StoreSelectorParent):

    def selectStore(self, url, isLiteCalculate = False):
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

        if isLiteCalculate:
            item['siteName'] = site
            item['id'] = item_id
            item['page'] = url
            item['endTime'] = datetime.now() + relativedelta(years=3)

            return ProductInfoClass(**item)
        
        if site == OrdersConsts.Stores.makeship:
            item = StoresApi.parseMakeshipItem(url = url)
        elif site == OrdersConsts.Stores.youtooz:
            item = YoutoozApi.parseYoutoozItem(url = url)
        elif site == OrdersConsts.Stores.plushshop:
            item = StoresApi.parsePlushShopItem(url = url, item_id = item_id)
        elif site in [OrdersConsts.Stores.amazon, OrdersConsts.Stores.amazonShort]:
            item = AmazonApi.parseAmazonItem(url = url, item_id = item_id)
        elif site == OrdersConsts.Stores.bratz:
            item = StoresApi.parseBratzItem(url = url)
        elif site == OrdersConsts.Stores.fangamer:
            item = StoresApi.parseFangamerItem(url = url)
        elif site == OrdersConsts.Stores.mattel:
            item = StoresApi.parseMattelItem(url = url)
        
        return ProductInfoClass(**item)
    
