from APIs.webUtils import WebUtils 
import requests
from confings.Consts import ShipmentPriceType as spt
from datetime import datetime
from dateutil.relativedelta import relativedelta
import locale
import json
import time 
from SQLS.DB_Operations import GetNotSeenProducts, insertNewSeenProducts
from random import choice
from confings.Consts import MonitorStoresType
from pprint import pprint
from requests_html import HTMLSession 
from confings.Consts import Stores
import cfscrape 
from seleniumbase import Driver
from APIs.posredApi import PosredApi
import random
import sys
from concurrent.futures import ThreadPoolExecutor
sys.argv.append("-n")  # Tell SeleniumBase to do thread-locking as needed

class AmiAmiApi():

    driver = [0, 1, 2, 3]

    @staticmethod
    def startDriver(thread_index):

        AmiAmiApi.driver[thread_index] = WebUtils.getSelenium(isUC=True)
        AmiAmiApi.driver[thread_index].open('https://www.amiami.com/eng/')  #https://www.amiami.com/eng/
        time.sleep(30)
        AmiAmiApi.driver[thread_index].save_screenshot("screenshot.png")

    @staticmethod
    def stopDriver(thread_index):
        AmiAmiApi.driver[thread_index].quit()

    @staticmethod
    def refreshDriver(thread_index):
        AmiAmiApi.driver[thread_index].refresh()

    AMI_API_ITEM_INFO = 'https://api.amiami.com/api/v1.0/item?gcode={}'

    # 9882 - Fashion
    wrongCategoriesNumbers = [9882]
    wrongCategoriesNumbersCate3 = [8545]


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
    def isWrongCategoryName(item_name):
        """Определить неинтересующие категории по названию товара

        Args:
            item_name (string): название товара

        Returns:
            boolean: принадлженость к неинтересующим категориям
        """

        wrongCategoriesNames = ['Wall Scroll', 'T-shirt', 'Sweatshirt', 'Nice Body Smartphone Stand',
                                'Pillow Cover', 'Clear File', 'Sticker', 'Cycling Jersey', 'Hoodie', 'iPhone Case',
                                 'Pass Case', 'Bed Sheet', 'Duvet Cover', 'Towel Blanket', 'Rubber Mat', 'COSPA', 'Canvas Art' ]
                
        for wrongCategory in wrongCategoriesNames:
            if item_name.find(wrongCategory) > -1:
                return True
            

        return False
    
    @staticmethod
    def isWrongCategoryNumber(item_id):
        """Определить неинтересующие категории числовые

        Args:
            item_id (string): айди лота

        Returns:
            boolean: принадлженость к неинтересующим категориям
        """
        
        time.sleep(1)
        additionalInfo = AmiAmiApi.getAdditionalProductInfo(item_id = item_id)
        if additionalInfo['cate1'] in AmiAmiApi.wrongCategoriesNumbers or additionalInfo['sname'] in AmiAmiApi.wrongCategoriesNames:
            return True   

        return False
    
    @staticmethod
    def curlManyPages(curl, length, thread_index):
        """Запарсить несколько страниц

        Args:
            curl (string): строка запроса API
            length (int): количество необходимых страниц

        Returns:
            dict: словарь с инфой о товарах
        """

        js = {}
        for i in range(0, length):
            time.sleep(3)
            try:
                js_raw = AmiAmiApi.curlAmiAmiEng(curl.format(i+1), thread_index)
                if i == 0:
                    js = js_raw
                else:            
                    js['items'].extend(js_raw['items'])

            except Exception as e:
                pprint(e)
                continue
            
        return js

    @staticmethod
    def curlAmiAmiEng(curl, thread_index):
        """Запрос к API AmiAmiEng

        Args:
            curl (string): строка запроса API

        Returns:
            dict: словарь с результатом запроса
        """

        headers = {}
        headers['Accept'] = '*/*'
        headers['Access-Control-Request-Headers']= 'x-user-key'
        headers['x-user-key'] = 'amiami_dev'
        headers['Sec-Fetch-Dest'] = 'empty'
        headers['Sec-Fetch-Mode'] = 'cors'
        headers['Sec-Fetch-Site'] = 'same-site'
        headers['Referer'] = 'https://www.amiami.com/'
        headers['Origin'] = 'https://www.amiami.com'
        headers['Sec-Ch-Ua-Mobile'] = '?0'
        headers['Allow-Control-Allow-Origin'] = '*'
       
        #req1= f"""let [resolve] = arguments; fetch('{curl}'""" + """ , {method: 'GET', headers:""" + f"""{headers}""" + """}).then(r => resolve(r.json()))"""
        req1= f"""let result = await fetch('{curl}'""" + """ , {method: 'GET', headers:""" + f"""{headers}""" + """}).then(r => r.json()); return result;"""

        result = AmiAmiApi.driver[thread_index].execute_script(req1)

        '''
        if not result['RSuccess']:
            pprint('trying again')
            AmiAmiApi.refreshDriver(thread_index=thread_index)
            time.sleep(30)
            AmiAmiApi.curlAmiAmiEng(curl=curl, thread_index=thread_index)
        '''   
        return result   

    @staticmethod
    def parseAmiAmiEng(url, item_id, thread_index):
        """Получение базовой информации о лоте с магазина AmiAmi

        Args:
            url (string): ссылка на лот
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        curl = AmiAmiApi.AMI_API_ITEM_INFO.format(item_id)
        
        js = AmiAmiApi.curlAmiAmiEng(curl, thread_index = thread_index)

        item = {}
        item['itemPrice'] = js['item']['price']
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = spt.undefined
        item['page'] = url
        item['mainPhoto'] = 'https://img.amiami.com'+js['item']['main_image_url']
        item['name'] = js['item']['gname']
        item['endTime'] = datetime.now() + relativedelta(years=3)

        commission = PosredApi.getСommissionForItem(item['page'])
        item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
        item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice'])  

        item['siteName'] = Stores.amiAmi
        item['id'] = item_id   

        return item

    @staticmethod
    def parseAmiAmiEngSimple(url, item_id):
        """Получение базовой информации о лоте с магазина AmiAmi через html

        Args:
            url (string): ссылка на лот

        Returns:
            dict: словарь с информацией о лоте
        """
        soup = WebUtils.getSoup(url = url, isUcSeleniumNeeded = True)

        pprint(soup.find('p', class_ = 'item-detail__price'))

        item = {}
        item['itemPrice'] = soup.find('span', class_ = 'item-detail__price_selling-price').text
        item['itemPrice'] = int(item['itemPrice'].replace(',', ''))

        item['tax'] = 0
        item['itemPriceWTax'] = 0 # Всегда включена в цену
        item['shipmentPrice'] = spt.undefined
        item['page'] = url
        item['mainPhoto'] = soup.find('a', class_ = 'nolink sponly')['src']
        item['name'] = soup.find('h2', class_ = 'item-detail__section-title').text
        item['endTime'] = datetime.now() + relativedelta(years=3)

        commission = PosredApi.getСommissionForItem(item['page'])
        item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
        item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice'])  

        item['siteName'] = Stores.amiAmi
        item['id'] = item_id   

        return item
    

    @staticmethod
    def parseAmiAmiJp(url, item_id):
        """Получение базовой информации о лоте с магазина AmiAmi Jp

        Args:
            url (string): ссылка на лот

        Returns:
            dict: словарь с информацией о лоте
        """
        soup = WebUtils.getSoup(url = url, isUcSeleniumNeeded = True)

        item = {}
        item['itemPrice'] = soup.find('div', class_ = 'price').text
        item['itemPrice'] = int(item['itemPrice'].split('円')[0].replace('\t', '').replace('\n', '').replace(',', '').split('OFF')[-1])

        item['tax'] = 0
        item['itemPriceWTax'] = 0 # Всегда включена в цену
        item['shipmentPrice'] = spt.undefined
        item['page'] = url
        item['mainPhoto'] = soup.find('img', class_ = 'gallery_item_main ofi')['src']
        item['name'] = soup.find('h2', class_ = 'heading_10').text
        item['endTime'] = datetime.now() + relativedelta(years=3)

        commission = PosredApi.getСommissionForItem(item['page'])
        item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
        item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice'])  

        item['siteName'] = Stores.amiAmi
        item['id'] = item_id   

        return item
    
        
    @staticmethod
    def getAdditionalProductInfo(item_id, thread_index):
        """Получить доп инфо по товару

        Args:
            item_id (string): айди лота

        Returns:
            dict: словарь с доп инфой о товаре
        """

        curl = AmiAmiApi.AMI_API_ITEM_INFO.format(item_id)

        # пока не получим норм результат
        for i in range(5):
            try:
                time.sleep(2)
                js = AmiAmiApi.curlAmiAmiEng(curl, thread_index)

                item_info = {}
                item_info['sname'] = js['item']['sname'].replace('(Released)', '').replace('Pre-owned ','')
                item_info['cate1'] =  js['item']['cate1'][0]
                
                locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
                item_info['releasedate'] =  js['item']['releasedate'].split(' ')[-1] if js['item']['releasedate'].find(' ') > -1 else js['item']['releasedate']
                try:
                    item_info['releasedate'] =  datetime.strptime(item_info['releasedate'], '%b-%Y') if item_info['releasedate'] else 'Неизвестно'
                except:
                    item_info['releasedate'] =  datetime.strptime(item_info['releasedate'], '%Y')
                return item_info
            
            except Exception as e:
                pprint(e)
                continue

        return 0

    @staticmethod
    def productsAmiAmiEng(type_id, thread_index, logger = ''):
        """Получение списка товаров из Sale категории AmiAmiEng

        Args:
            type_id (str): категория парсинга.

        Returns:
            list of dict: список товаров и инфо о них
        """

        pages_to_see = 15

        if type_id == MonitorStoresType.amiAmiEngSale:
            curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_saleitem=1&s_st_list_newitem_available=1'
            pages_to_see = 10
        else:
            curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_list_newitem_available=1'

        js = AmiAmiApi.curlManyPages(curl, pages_to_see, thread_index)

        item_list_raw = []
        item_list_ids = []
        item_list = []

        for product in js['items']:

            if type_id == MonitorStoresType.amiAmiEngInStock and (product['preorderitem'] 
                                                                  or product['saleitem'] 
                                                                  or not product['thumb_url']):
                continue
            
            item = {}
            item['itemPrice'] = product['min_price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0
            item['shipmentPrice'] = spt.undefined
            item['page'] = f"https://www.amiami.com/eng/detail?gcode={product['gcode']}"
            item['mainPhoto'] = 'https://img.amiami.com'+product['thumb_url']
            item['itemId'] = product['gcode']
            item['name'] = product['gname']

            if AmiAmiApi.isWrongCategory(product['gcode']) or product['image_on'] == 0:
                continue
            item_list_raw.append(item.copy())

        logger.info(f"[SEEN-{type_id}-PRERAW] len {len(item_list_raw)}")
        
        if item_list_raw:
            
            item_list_ids = GetNotSeenProducts([item['itemId'] for item in item_list_raw], type_id= type_id)

            logger.info(f"[SEEN-{type_id}-RAW] len {len(item_list_ids)}")

            for item in item_list_raw:
                time.sleep(3)
                if not item['itemId'] in item_list_ids:
                    continue
                
                additionalInfo = AmiAmiApi.getAdditionalProductInfo(item['itemId'], thread_index)
                if not additionalInfo:
                    continue
                elif additionalInfo['cate1'] in AmiAmiApi.wrongCategoriesNumbers or AmiAmiApi.isWrongCategoryName(additionalInfo['sname']):
                    insertNewSeenProducts([item['itemId']], type_id = type_id)
                    continue

                item_list.append(item.copy())
        
        return item_list
    
    @staticmethod
    def preOrderAmiAmiEng(type_id, thread_index, logger = ''):

        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        
        curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_list_preorder_available=1'

        
        #js = AmiAmiApi.curlManyPages(curl, 20, thread_index)
        js = AmiAmiApi.curlManyPages(curl, 10, thread_index)

        item_list_raw = []
        item_list_ids = []
        item_list = []

        for preOrder in js['items']:
            
            if not preOrder['preorderitem'] or not preOrder['thumb_url']:
                continue 

            item = {}
            item['itemPrice'] = preOrder['min_price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0
            item['shipmentPrice'] = spt.undefined
            item['page'] = f"https://www.amiami.com/eng/detail?gcode={preOrder['gcode']}"
            item['mainPhoto'] = 'https://img.amiami.com'+preOrder['thumb_url']
            item['itemId'] = preOrder['gcode']


            item['name'] = preOrder['gname']
            try:
                item['releaseDate'] = datetime.strptime(preOrder['releasedate'] , '%Y-%m-%d %H:%M:%S')
            except:
                continue
            
            if item['releaseDate'].month == datetime.now().month and item['releaseDate'].year == datetime.now().year:
                continue

            if AmiAmiApi.isWrongCategory(preOrder['gcode']):
                insertNewSeenProducts([item['itemId']], type_id = type_id)
                continue
            if preOrder['image_on'] == 0:
                continue

            item_list_raw.append(item.copy())

        
        logger.info(f"[SEEN-{type_id}-PRERAW] len {len(item_list_raw)}")
        
        if item_list_raw:
            item_list_ids = GetNotSeenProducts([item['itemId'] for item in item_list_raw], type_id= type_id)
        
            logger.info(f"[SEEN-{type_id}-RAW] len {len(item_list_ids)}")
           

            for item in item_list_raw:

                time.sleep(3)
                if not item['itemId'] in item_list_ids:
                    continue
                
                additionalInfo = AmiAmiApi.getAdditionalProductInfo(item['itemId'], thread_index)
                if not additionalInfo:
                    continue
                elif additionalInfo['cate1'] in AmiAmiApi.wrongCategoriesNumbers or AmiAmiApi.isWrongCategoryName(additionalInfo['sname']):
                    insertNewSeenProducts([item['itemId']], type_id = type_id)
                    continue

                locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

                if item['releaseDate']  < datetime.now() - relativedelta(months=1):
                    
                    item['releaseDate'] =  additionalInfo['releasedate'].strftime("%b %Y")

                else:
                    item['releaseDate'] = item['releaseDate'].strftime("%b %Y")

                item_list.append(item.copy())

        return item_list        
    
    @staticmethod
    def preownedAmiAmiEng(type_id, logger = '', thread_index = 0):
        """Получение списка товаров из PreOwned категории AmiAmiEng

        Args:
            type_id (str): категория парсинга.

        Returns:
            list of dict: список товаров и инфо о них
        """
        
        curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_sortkey=preowned&s_st_condition_flg=1&s_st_list_newitem_available=1'
      
        js = AmiAmiApi.curlManyPages(curl, 15, thread_index)

        item_list = []
        item_list_ids = []
        item_list_raw = []

        for preowned in js['items']:
            
            if not preowned['instock_flg'] or not preowned['thumb_url']:
                continue 

            item = {}
            item['itemPrice'] = preowned['min_price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0
            item['shipmentPrice'] = spt.undefined
            item['page'] = f"https://www.amiami.com/eng/detail?gcode={preowned['gcode']}"
            item['mainPhoto'] = 'https://img.amiami.com'+preowned['thumb_url']
            item['itemId'] = preowned['gcode']

            if AmiAmiApi.isWrongCategory(preowned['gcode']) or preowned['image_on'] == 0:
                continue

            item_list_raw.append(item.copy())

        logger.info(f"[SEEN-{type_id}-PRERAW] len {len(item_list_raw)}")
        
        if item_list_raw:
            item_list_ids = GetNotSeenProducts([item['itemId'] for item in item_list_raw], type_id= type_id)
            item_list_raw = [item for item in item_list_raw if item['itemId'] in item_list_ids]

            logger.info(f"[SEEN-{type_id}-RAW] len {len(item_list_ids)}: {item_list_ids}")

            for item in item_list_raw:
                time.sleep(3)
                
                additionalInfo = AmiAmiApi.getAdditionalProductInfo(item['itemId'], thread_index)
                
                if not additionalInfo:
                    continue
                elif additionalInfo['cate1'] in AmiAmiApi.wrongCategoriesNumbers or AmiAmiApi.isWrongCategoryName(additionalInfo['sname']):
                    insertNewSeenProducts([item['itemId']], type_id = type_id)
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
        