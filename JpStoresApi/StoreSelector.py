from pprint import pprint
import re
from confings.Consts import RegexType
from JpStoresApi.yahooApi import getAucInfo
from JpStoresApi.SecondaryStoresApi import SecondaryStoreApi as ssa
from JpStoresApi.StoresApi import StoreApi as sa
from JpStoresApi.AmiAmiApi import AmiAmiApi

import json
from confings.Consts import PRIVATES_PATH

class StoreSelector:

    class Stores:

        mercari = 'mercari'
        payPay = 'paypayfleamarketyahoo'
        yahooAuctions = 'pageauctionsyahoo'
        amiAmi = 'amiami'
        mandarake = 'mandarake'
        animate = 'animate-onlineshop'


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

        if site == self.Stores.mercari:
            item = ssa.parseMercariPage(url, self.getItemID())

        elif site == self.Stores.payPay:
            item = ssa.parsePayPay(url, self.getItemID())

        elif site == self.Stores.yahooAuctions:
            
            tmp_dict = json.load(open(PRIVATES_PATH, encoding='utf-8'))
            app_id = tmp_dict['yahoo_jp_app_id']
            item = getAucInfo(app_id= app_id,id = self.getItemID())

        elif site == self.Stores.amiAmi:
            pprint(self.Stores.amiAmi)
            
            if url.find('/eng/')>0:
                item = AmiAmiApi.parseAmiAmiEng(url, self.getItemID().split("=")[-1])
            else:
                item = ''
                item = AmiAmiApi.parseAmiAmiJp(url)
            
        elif site == self.Stores.mandarake:
            item = ssa.parseMandarake(url)

        elif site == self.Stores.animate:
            
            item = sa.parseAnimate(self.getItemID())


        return item
    
