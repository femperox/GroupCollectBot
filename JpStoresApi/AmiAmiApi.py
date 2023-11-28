from APIs.webUtils import WebUtils 
import requests
from confings.Consts import ShipmentPriceType as spt
from datetime import datetime
from dateutil.relativedelta import relativedelta
import locale
import json
import time 
from SQLS.DB_Operations import GetNotSeenProducts
from random import choice
from confings.Consts import MonitorStoresType
from pprint import pprint

class AmiAmiApi():

    AMI_API_ITEM_INFO = 'https://api.amiami.com/api/v1.0/item?gcode={}'

    # 9882 - Fashion
    wrongCategoriesNumbers = [9882]

    @staticmethod
    def isWrongCategory(item_id):
        """Определить неинтересующие категории

        Args:
            item_id (string): айди лота

        Returns:
            boolean: принадлженость к неинтересующим категориям
        """

        wrongCategories = ['CARD', 'TC-IDL',
                           'TOY-SCL', 'RAIL', 
                           'MED', 'JIGS', 
                           'TOY-RBT', 'TOL', 'TOY']
        
        for wrongCategory in wrongCategories:
            if item_id.find(wrongCategory) > -1:
                return True

        return False
    
    @staticmethod
    def isWrongCategoryNumber(item_id, proxy = ''):
        """Определить неинтересующие категории числовые

        Args:
            item_id (string): айди лота
            proxy (str, optional): прокси. Defaults to ''.

        Returns:
            boolean: принадлженость к неинтересующим категориям
        """
        
        time.sleep(1)
        if AmiAmiApi.getAdditionalProductInfo(item_id = item_id, proxy = proxy)['cate1'] in AmiAmiApi.wrongCategoriesNumbers:
            return True   

        return False
    
    @staticmethod
    def curlManyPages(curl, length, proxy):
        """Запарсить несколько страниц

        Args:
            curl (string): строка запроса API
            length (int): количество необходимых страниц
            proxy (string): прокси

        Returns:
            dict: словарь с инфой о товарах
        """
        
        js = {}
        for i in range(0, length):
            time.sleep(3)
            js_raw = AmiAmiApi.curlAmiAmiEng(curl.format(i+1), proxy)
            if i == 0:
                js = js_raw
            else:
                js['items'].extend(js_raw['items'])
            
            
        
        return js



    @staticmethod
    def curlAmiAmiEng(curl, proxy = ''):
        """Запрос к API AmiAmiEng

        Args:
            curl (string): строка запроса API

        Returns:
            dict: словарь с результатом запроса
        """

        headers = WebUtils.getHeader()
        headers['x-user-key'] = 'amiami_dev'

        session = requests.session()
        page = session.get(curl, headers = headers, proxies = {'http': f'http://{proxy}'} if proxy else None)

        return json.loads(page.content)     

    @staticmethod
    def parseAmiAmiEng(url, item_id):
        """Получение базовой информации о лоте с магазина AmiAmi

        Args:
            url (string): ссылка на лот
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        curl = AmiAmiApi.AMI_API_ITEM_INFO.format(item_id)
        
        js = AmiAmiApi.curlAmiAmiEng(curl)

        item = {}
        item['itemPrice'] = js['item']['price']
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = spt.undefined
        item['page'] = url
        item['mainPhoto'] = 'https://img.amiami.com'+js['item']['main_image_url']
        item['siteName'] = 'AmiAmiEng'
        item['name'] = js['item']['gname']

        return item

    @staticmethod
    def parseAmiAmiJp(url):
        """Получение базовой информации о лоте с магазина AmiAmi Jp

        Args:
            url (string): ссылка на лот

        Returns:
            dict: словарь с информацией о лоте
        """

        soup = WebUtils.getSraper(url)
        name = soup.find('img', class_='gallery_item_main ofi')['alt']
        price = int(soup.find('div', class_='price').text.replace(',', '').replace('\t', '').split('円')[0].split('\n')[-1])
        img = soup.find('img', class_='gallery_item_main ofi')['src']

        item = {}
        
        item['itemPrice'] = price
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = spt.undefined
        item['page'] = url
        item['mainPhoto'] = img
        item['siteName'] = 'AmiAmiJp'
        item['name'] = name
        
        return item
    

        
    @staticmethod
    def getAdditionalProductInfo(item_id, proxy=''):
        """Получить доп инфо по товару

        Args:
            item_id (string): айди лота
            proxy (str, optional): прокси. Defaults to ''.

        Returns:
            dict: словарь с доп инфой о товаре
        """

        curl = AmiAmiApi.AMI_API_ITEM_INFO.format(item_id)

        js = AmiAmiApi.curlAmiAmiEng(curl, proxy)

        item_info = {}
        item_info['sname'] = js['item']['sname'].replace('(Released)', '').replace('Pre-owned ','')
        item_info['cate1'] =  js['item']['cate1'][0]
        
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        item_info['releasedate'] =  js['item']['releasedate'].split(' ')[-1] if js['item']['releasedate'].find(' ') > -1 else js['item']['releasedate']
        item_info['releasedate'] =  datetime.strptime(item_info['releasedate'], '%b-%Y') if item_info['releasedate'] else 'Неизвестно'

        return item_info

    @staticmethod
    def productsAmiAmiEng(type_id, proxy = ''):
        """Получение списка товаров из Sale категории AmiAmiEng

        Args:
            type_id (str): категория парсинга.
            proxy (str, optional): прокси. Defaults to ''.

        Returns:
            list of dict: список товаров и инфо о них
        """

        pages_to_see = 7

        if type_id == MonitorStoresType.amiAmiEngSale:
            curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=7001216802&ransu=vM4sX7Eyhya2Bj6bBa0jahnlpEFaqi57&age_confirm=&s_st_saleitem=1&s_st_list_newitem_available=1'
            pages_to_see = 5
        else:
            curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_list_newitem_available=1'

        js = AmiAmiApi.curlManyPages(curl, pages_to_see, proxy)

        item_list = []
        for product in js['items']:

            if type_id == MonitorStoresType.amiAmiEngInStock and (product['preorderitem'] or product['saleitem']):
                continue
            
            item = {}
            item['itemPrice'] = product['min_price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0
            item['shipmentPrice'] = spt.undefined
            item['page'] = f"https://www.amiami.com/eng/detail?gcode={product['gcode']}"
            item['mainPhoto'] = 'https://img.amiami.com'+product['thumb_url']
            item['siteName'] = 'AmiAmiEng'
            item['itemId'] = product['gcode']
            item['name'] = product['gname']

            if AmiAmiApi.isWrongCategory(product['gcode']) or product['image_on'] == 0:
                continue
            item_list.append(item.copy())

        item_list_ids = GetNotSeenProducts([item['itemId'] for item in item_list], type_id= type_id)
        
        if item_list_ids: 
            proxies = WebUtils.getProxyServerNoSelenium(type_needed = ['socks4', 'socks5'])

        item_list = [item for item in item_list if item['itemId'] in item_list_ids and not AmiAmiApi.isWrongCategoryNumber(item['itemId'], choice(proxies))]
        
        return item_list
    
    @staticmethod
    def preOrderAmiAmiEng(type_id, proxy = ''):

        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        
        curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_list_preorder_available=1&s_st_list_newitem_available=1'

        js = AmiAmiApi.curlManyPages(curl, 7, proxy)

        item_list_raw = []
        for preOrder in js['items']:
            
            if not preOrder['preorderitem']:
                continue 

            item = {}
            item['itemPrice'] = preOrder['min_price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0
            item['shipmentPrice'] = spt.undefined
            item['page'] = f"https://www.amiami.com/eng/detail?gcode={preOrder['gcode']}"
            item['mainPhoto'] = 'https://img.amiami.com'+preOrder['thumb_url']
            item['siteName'] = 'AmiAmiEng'
            item['itemId'] = preOrder['gcode']
            item['name'] = preOrder['gname']
            item['releaseDate'] = datetime.strptime(preOrder['releasedate'] , '%Y-%m-%d %H:%M:%S')
            
            if item['releaseDate'].month == datetime.now().month:
                continue

            if AmiAmiApi.isWrongCategory(preOrder['gcode']) or preOrder['image_on'] == 0:
                continue

            item_list_raw.append(item.copy())

        
        if item_list_raw:
            item_list_ids = GetNotSeenProducts([item['itemId'] for item in item_list_raw], type_id= type_id)
        item_list = []

        if item_list_ids: 
            proxies = WebUtils.getProxyServerNoSelenium(type_needed = ['socks4', 'socks5'])

        for item in item_list_raw:
            time.sleep(1)
            if not item['itemId'] in item_list_ids:
                continue
            
            additionalInfo = AmiAmiApi.getAdditionalProductInfo(item['itemId'], choice(proxies))
            
            if additionalInfo['cate1'] in AmiAmiApi.wrongCategoriesNumbers:
                continue

            locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

            if item['releaseDate']  < datetime.now() - relativedelta(months=1):
                
                item['releaseDate'] =  additionalInfo['releasedate'].strftime("%b %Y")

            else:
                item['releaseDate'] = item['releaseDate'].strftime("%b %Y")

            item_list.append(item.copy())

 
        return item_list        
    
    @staticmethod
    def preownedAmiAmiEng(type_id, proxy = ''):
        """Получение списка товаров из PreOwned категории AmiAmiEng

        Args:
            type_id (str): категория парсинга.
            proxy (str, optional): прокси. Defaults to ''.

        Returns:
            list of dict: список товаров и инфо о них
        """
        
        curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_sortkey=preowned&s_st_condition_flg=1&s_st_list_newitem_available=1'

        js = AmiAmiApi.curlManyPages(curl, 4, proxy)

        item_list = []
        for preowned in js['items']:
            
            if not preowned['instock_flg']:
                continue 

            item = {}
            item['itemPrice'] = preowned['min_price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0
            item['shipmentPrice'] = spt.undefined
            item['page'] = f"https://www.amiami.com/eng/detail?gcode={preowned['gcode']}"
            item['mainPhoto'] = 'https://img.amiami.com'+preowned['thumb_url']
            item['siteName'] = 'AmiAmiEng'
            item['itemId'] = preowned['gcode']

            if AmiAmiApi.isWrongCategory(preowned['gcode']) or preowned['image_on'] == 0:
                continue

            item_list.append(item.copy())

        item_list_ids = GetNotSeenProducts([item['itemId'] for item in item_list], type_id= type_id)
        item_list_raw = [item for item in item_list if item['itemId'] in item_list_ids]
        item_list = []

        if item_list_ids: 
            proxies = WebUtils.getProxyServerNoSelenium(type_needed = ['socks4', 'socks5'])

        for item in item_list_raw:
            time.sleep(1)
            additionalInfo = AmiAmiApi.getAdditionalProductInfo(item['itemId'], proxy = choice(proxies))
            if additionalInfo['cate1'] in AmiAmiApi.wrongCategoriesNumbers:
                continue
            item['name'] = additionalInfo['sname']
            item_list.append(item.copy())
        
        return item_list
    

    @staticmethod
    def packageDamageAmiAmiEng(type_id, proxy = ''):
        """Получение списка товаров из package damage категории AmiAmiEng

        Args:
            url (string): ссылка на лот

        Returns:
            dict: словарь с информацией о лоте
        """
        # TODO. Подумать
        
        curl = 'https://www.amiami.com/eng/c/sale/'
        curl2 = 'https://www.amiami.com/_nuxt/pages__lang_c_sale.7b456c13cfd19f570716.js'

        headers = WebUtils.getHeader()
        headers['x-user-key'] = 'amiami_dev'

        session = requests.session()
        page = session.get(curl2, headers = headers, proxies = {'http': f'http://{proxy}'} if proxy else None)        

        return page.content

        # TODO
        