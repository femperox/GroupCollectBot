from pprint import pprint
from confings.Consts import OrdersConsts
from APIs.StoresApi.StoreSelectorParent import StoreSelectorParent
from APIs.StoresApi.USStoresApi.StoresApi import StoresApi
from APIs.StoresApi.USStoresApi.YoutoozApi import YoutoozApi
from APIs.StoresApi.USStoresApi.AmazonApi import AmazonApi
from datetime import datetime
from dateutil.relativedelta import relativedelta
from APIs.StoresApi.ProductInfoClass import ProductInfoClass
from APIs.StoresApi.USStoresApi.EbayApi import EbayApi

class StoreSelector(StoreSelectorParent):

    def selectStore(self, url, isLiteCalculate = False, isAdmin = False):
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

            return ProductInfoClass(**item)
        if not isAdmin and site in OrdersConsts.Stores.bannedStoresUs:
            return ProductInfoClass(**item)
                
        if site == OrdersConsts.Stores.makeship:
            item = StoresApi.parseMakeshipItem(url = url)
        elif site == OrdersConsts.Stores.youtooz:
            item = YoutoozApi.parseYoutoozItem(url = url)
        elif site == OrdersConsts.Stores.plushshop:
            item = StoresApi.parsePlushShopItem(url = url, item_id = item_id)
        elif site in [OrdersConsts.Stores.amazon, OrdersConsts.Stores.amazonShort]:
            item = AmazonApi.parseAmazonItemWProxy(url = url, item_id = item_id)
        elif site == OrdersConsts.Stores.bratz:
            item = StoresApi.parseBratzItem(url = url)
        elif site == OrdersConsts.Stores.fangamer:
            item = StoresApi.parseFangamerItem(url = url)
        elif site == OrdersConsts.Stores.mattel:
            item = StoresApi.parseMattelItem(url = url)
        elif site == OrdersConsts.Stores.plushwonderland:
            item = StoresApi.parsePlushWonderlandItem(url = url)
        elif site == OrdersConsts.Stores.ebay:
            item = EbayApi.parseEbayItem(url = url)
        elif site == OrdersConsts.Stores.hottopic:
            item = StoresApi.parseHotTopicItem(url = url)
        else:
            self.url = url
            randmoStoreName = self.getStoreName()
            item = StoresApi.parseJsonRandomStoreItem(url = url, storeName = randmoStoreName)
        

        item = ProductInfoClass(**item)
        item.set_country(country = OrdersConsts.OrderTypes.user if site in [OrdersConsts.Stores.makeship, OrdersConsts.Stores.plushshop, OrdersConsts.Stores.plushwonderland] else OrdersConsts.OrderTypes.us)
        return item