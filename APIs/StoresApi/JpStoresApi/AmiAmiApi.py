from APIs.webUtils import WebUtils 
from confings.Consts import OrdersConsts
from datetime import datetime
from dateutil.relativedelta import relativedelta
import locale
import time 
from SQLS.DB_Operations import GetNotSeenProducts, insertNewSeenProducts
from pprint import pprint
from APIs.PosredApi.posredApi import PosredApi
from APIs.StoresApi.ProductInfoClass import ProductInfoClass
from curl_cffi import requests

class AmiAmiApi():

    AMI_API_ITEM_INFO = 'https://api.amiami.com/api/v1.0/item?gcode={}'
    AMI_API_ITEM_INFO2 = 'https://api.amiami.com/api/v1.0/item?scode={}'

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
    def curlManyPages(curl, length):
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
                js_raw = requests.get(curl, headers = WebUtils.getHeader(isAmiAmi = True), impersonate="chrome110").json()
                pprint(js_raw)
                if i == 0:
                    js = js_raw
                else:            
                    js['items'].extend(js_raw['items'])

            except Exception as e:
                pprint(e)
                continue
            
        return js

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

        js = requests.get(curl, headers = WebUtils.getHeader(isAmiAmi = True), impersonate="chrome110",).json()
        
        item = {}
        item['itemPrice'] = js['item']['price']
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
        item['page'] = url
        item['mainPhoto'] = 'https://img.amiami.com'+js['item']['main_image_url']
        item['name'] = js['item']['gname']

        commission = PosredApi.getСommissionForItem(item['page'])
        item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
        item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice'])  

        item['siteName'] = OrdersConsts.Stores.amiAmi
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
        item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
        item['page'] = url
        item['mainPhoto'] = soup.find('img', class_ = 'gallery_item_main ofi')['src']
        item['name'] = soup.find('h2', class_ = 'heading_10').text

        commission = PosredApi.getСommissionForItem(item['page'])
        item['posredCommission'] = commission['posredCommission'].format(item['itemPrice'])
        item['posredCommissionValue'] = commission['posredCommissionValue'](item['itemPrice'])  

        item['siteName'] = OrdersConsts.Stores.amiAmi
        item['id'] = item_id   

        return item
    
        
    @staticmethod
    def getAdditionalProductInfo(item_id):
        """Получить доп инфо по товару

        Args:
            item_id (string): айди лота

        Returns:
            dict: словарь с доп инфой о товаре
        """

        curl = AmiAmiApi.AMI_API_ITEM_INFO.format(item_id)

        try:
            time.sleep(2)
            js = requests.get(curl, headers = WebUtils.getHeader(isAmiAmi = True), impersonate="chrome110").json()

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

        return 0

    @staticmethod
    def productsAmiAmiEng(type_id, logger = ''):
        """Получение списка товаров из Sale категории AmiAmiEng

        Args:
            type_id (str): категория парсинга.

        Returns:
            list of dict: список товаров и инфо о них
        """

        pages_to_see = 15

        if type_id == OrdersConsts.MonitorStoresType.amiAmiEngSale:
            curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_saleitem=1&s_st_list_newitem_available=1'
            pages_to_see = 10
        else:
            curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_list_newitem_available=1'

        js = AmiAmiApi.curlManyPages(curl, pages_to_see)

        item_list_raw = []
        item_list_ids = []
        item_list = []

        for product in js['items']:

            if type_id == OrdersConsts.MonitorStoresType.amiAmiEngInStock and (product['preorderitem'] 
                                                                  or product['saleitem'] 
                                                                  or not product['thumb_url']):
                continue
            
            item = {}
            item['itemPrice'] = product['min_price']
            item['tax'] = 0
            item['itemPriceWTax'] = 0
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
            item['page'] = f"https://www.amiami.com/eng/detail?gcode={product['gcode']}"
            item['mainPhoto'] = 'https://img.amiami.com'+product['thumb_url']
            item['id'] = product['gcode']
            item['name'] = product['gname']

            if AmiAmiApi.isWrongCategory(product['gcode']) or product['image_on'] == 0:
                continue
            item_list_raw.append(ProductInfoClass(**item))

        logger.info(f"[SEEN-{type_id}-PRERAW] len {len(item_list_raw)}")
        
        if item_list_raw:
            
            item_list_ids = GetNotSeenProducts([item.id for item in item_list_raw], type_id= type_id)

            logger.info(f"[SEEN-{type_id}-RAW] len {len(item_list_ids)}")

            for item in item_list_raw:
                time.sleep(3)
                if not item.id in item_list_ids:
                    continue
                
                additionalInfo = AmiAmiApi.getAdditionalProductInfo(item.id)
                if not additionalInfo:
                    continue
                elif additionalInfo['cate1'] in AmiAmiApi.wrongCategoriesNumbers or AmiAmiApi.isWrongCategoryName(additionalInfo['sname']):
                    insertNewSeenProducts([item.id], type_id = type_id)
                    continue

                item_list.append(item.copy())
        
        return item_list
    
    @staticmethod
    def preOrderAmiAmiEng(type_id, logger = ''):

        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        
        curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_st_list_preorder_available=1'

        js = AmiAmiApi.curlManyPages(curl, 10)

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
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
            item['page'] = f"https://www.amiami.com/eng/detail?gcode={preOrder['gcode']}"
            item['mainPhoto'] = 'https://img.amiami.com'+preOrder['thumb_url']
            item['id'] = preOrder['gcode']

            item['name'] = preOrder['gname']
            try:
                item['releaseDate'] = datetime.strptime(preOrder['releasedate'] , '%Y-%m-%d %H:%M:%S')
            except:
                continue
            
            if item['releaseDate'].month == datetime.now().month and item['releaseDate'].year == datetime.now().year:
                continue

            if AmiAmiApi.isWrongCategory(preOrder['gcode']):
                insertNewSeenProducts([item.id], type_id = type_id)
                continue
            if preOrder['image_on'] == 0:
                continue

            item_list_raw.append(ProductInfoClass(**item))

        
        logger.info(f"[SEEN-{type_id}-PRERAW] len {len(item_list_raw)}")
        
        if item_list_raw:
            item_list_ids = GetNotSeenProducts([item.id for item in item_list_raw], type_id= type_id)
        
            logger.info(f"[SEEN-{type_id}-RAW] len {len(item_list_ids)}")
           
            for item in item_list_raw:

                time.sleep(3)
                if not item.id in item_list_ids:
                    continue
                
                additionalInfo = AmiAmiApi.getAdditionalProductInfo(item.id)
                if not additionalInfo:
                    continue
                elif additionalInfo['cate1'] in AmiAmiApi.wrongCategoriesNumbers or AmiAmiApi.isWrongCategoryName(additionalInfo['sname']):
                    insertNewSeenProducts([item.id], type_id = type_id)
                    continue

                locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

                if item.releaseDate  < datetime.now() - relativedelta(months=1):
                    
                    item.setReleaseDate(releaseDate = additionalInfo['releasedate'].strftime("%b %Y"))

                else:
                    item.setReleaseDate(releaseDate = item['releaseDate'].strftime("%b %Y"))

                item_list.append(item.copy())

        return item_list        
    
    @staticmethod
    def preownedAmiAmiEng(type_id, logger = ''):
        """Получение списка товаров из PreOwned категории AmiAmiEng

        Args:
            type_id (str): категория парсинга.

        Returns:
            list of dict: список товаров и инфо о них
        """
        
        curl = 'https://api.amiami.com/api/v1.0/items?pagemax=50&pagecnt={}&lang=eng&mcode=&ransu=&age_confirm=&s_sortkey=preowned&s_st_condition_flg=1&s_st_list_newitem_available=1'
      
        js = AmiAmiApi.curlManyPages(curl, 25)

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
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
            item['page'] = f"https://www.amiami.com/eng/detail?gcode={preowned['gcode']}"
            item['mainPhoto'] = 'https://img.amiami.com'+preowned['thumb_url']
            item['id'] = preowned['gcode']

            if AmiAmiApi.isWrongCategory(preowned['gcode']) or preowned['image_on'] == 0:
                continue

            item_list_raw.append(ProductInfoClass(**item))

        logger.info(f"[SEEN-{type_id}-PRERAW] len {len(item_list_raw)}")
        
        if item_list_raw:
            item_list_ids = GetNotSeenProducts([item.id for item in item_list_raw], type_id= type_id)
            item_list_raw = [item for item in item_list_raw if item.id in item_list_ids]

            logger.info(f"[SEEN-{type_id}-RAW] len {len(item_list_ids)}: {item_list_ids}")

            for item in item_list_raw:
                time.sleep(3)
                
                additionalInfo = AmiAmiApi.getAdditionalProductInfo(item.id)
                
                if not additionalInfo:
                    continue
                elif additionalInfo['cate1'] in AmiAmiApi.wrongCategoriesNumbers or AmiAmiApi.isWrongCategoryName(additionalInfo['sname']):
                    insertNewSeenProducts([item.id], type_id = type_id)
                    continue

                item.setName(name = additionalInfo['sname'])
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
        