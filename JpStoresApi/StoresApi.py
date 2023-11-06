from APIs.webUtils import WebUtils 
import requests
from time import sleep
from pprint import pprint
from confings.Consts import ShipmentPriceType as spt

class StoreApi:

    @staticmethod
    def parseAnimate(item_id):
        """Получение базовой информации о лоте с магазина Animate

        Args:
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        curl = f'https://www.animate-onlineshop.jp/pd/{item_id}/'

        soup = WebUtils.getSoup(curl)
        name = soup.find('div', class_='item_overview_detail').find('h1').text
        price = int(soup.find('p', class_='price new_price fl_l').text.replace(',', '').split('円')[0])
        qnty = int(soup.find('input', id='lot')['value'])
        img = soup.find('div', class_='item_thumbs_inner').find('img')['src']

        item = {}
        item['itemPrice'] = price * qnty
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = spt.undefined
        item['page'] = curl
        item['mainPhoto'] = img
        item['siteName'] = 'Animate'
        item['name'] = name

        return item
    
    @staticmethod
    def parseAmiAmiEng(url, item_id):
        """Получение базовой информации о лоте с магазина AmiAmi

        Args:
            url (string): ссылка на лот
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        curl = f'https://api.amiami.com/api/v1.0/item?gcode={item_id}'#&lang=jp'

        headers = WebUtils.getHeader()
        headers['x-user-key'] = 'amiami_dev'

        session = requests.session()
        page = session.get(curl, headers=headers)
        
        js = page.json()

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

