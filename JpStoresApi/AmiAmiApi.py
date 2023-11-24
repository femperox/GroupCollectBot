from APIs.webUtils import WebUtils 
import requests
from confings.Consts import ShipmentPriceType as spt
from datetime import datetime
import locale
import json
import time 
from SQLS.DB_Operations import GetNotSeenProducts
from confings.Consts import MonitorStoresType

class AmiAmiApi():

    AMI_API_ITEM_INFO = 'https://api.amiami.com/api/v1.0/item?gcode={}'

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
                           'TOY-RBT', 'TOL']
        
        for wrongCategory in wrongCategories:
            if item_id.find(wrongCategory) > -1:
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

        headers = WebUtils.getHeader(isAmiAmi = True)

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
    def getFullPreownedName(item_id, proxy=''):
        """Получить полное название preOwned товара с АмиАми

        Args:
            item_id (string): айди лота
            proxy (str, optional): прокси. Defaults to ''.

        Returns:
            string: полное название айтема
        """

        curl = AmiAmiApi.AMI_API_ITEM_INFO.format(item_id)

        js = AmiAmiApi.curlAmiAmiEng(curl, proxy)

        return js['item']['sname'].replace('(Released)', '').replace('Pre-owned ','')

    @staticmethod
    def productsAmiAmiEng(type_id, proxy = ''):
        """Получение списка товаров из Sale категории AmiAmiEng

        Args:
            type_id (str): категория парсинга.
            proxy (str, optional): прокси. Defaults to ''.

        Returns:
            list of dict: список товаров и инфо о них
        """
        if type_id == MonitorStoresType.amiAmiEngSale:
            curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=7001216802&ransu=vM4sX7Eyhya2Bj6bBa0jahnlpEFaqi57&age_confirm=&s_st_saleitem=1'
        else:
            curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_list_newitem_available=1'

        js = AmiAmiApi.curlManyPages(curl, 2, proxy)

        item_list = []
        for product in js['items']:
            
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
        item_list = [item for item in item_list if item['itemId'] in item_list_ids]
        
        return item_list
    
    @staticmethod
    def preOrderAmiAmiEng(type_id, proxy = ''):

        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        
        curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_list_preorder_available=1'

        js = AmiAmiApi.curlManyPages(curl, 2, proxy)

        item_list = []
        for preOrder in js['items']:
            
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
            item['releaseDate'] = datetime.strptime(preOrder['releasedate'] , '%Y-%m-%d %H:%M:%S').strftime("%b %Y")

            if AmiAmiApi.isWrongCategory(preOrder['gcode']) or preOrder['image_on'] == 0:
                continue

            item_list.append(item.copy())

        item_list_ids = GetNotSeenProducts([item['itemId'] for item in item_list], type_id= type_id)
        item_list = [item for item in item_list if item['itemId'] in item_list_ids]
        
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
        
        curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt=1&lang=eng&mcode=&ransu=&age_confirm=&s_sortkey=preowned&s_st_condition_flg=1'

        js = AmiAmiApi.curlAmiAmiEng(curl, proxy)

        item_list = []
        for preowned in js['items']:
            
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
        item_list = [item for item in item_list if item['itemId'] in item_list_ids]

        for item in item_list:
            time.sleep(1)
            item['name'] = AmiAmiApi.getFullPreownedName(item['itemId'], proxy = proxy)
        
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

        headers = WebUtils.getHeader(isAmiAmi = True)

        session = requests.session()
        page = session.get(curl2, headers = headers, proxies = {'http': f'http://{proxy}'} if proxy else None)        

        return page.content

        # TODO
        