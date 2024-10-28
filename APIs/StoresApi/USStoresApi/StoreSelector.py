from pprint import pprint
from confings.Consts import Stores
from APIs.StoresApi.StoreSelectorParent import StoreSelectorParent
from APIs.StoresApi.USStoresApi.MakeShipApi import MakeShipApi
from APIs.StoresApi.USStoresApi.YoutoozApi import YoutoozApi
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

            return item

        if site == Stores.makeship:
            item = MakeShipApi.parseMakeshipItem(url = url)
        elif site == Stores.youtooz:
            item = YoutoozApi.parseYoutoozItem(url = url)

        
        return item
    