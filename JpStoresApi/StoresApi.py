from APIs.webUtils import WebUtils 
import requests
from time import sleep
from pprint import pprint

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
        price = int(soup.find('p', class_='price new_price fl_l').text.replace(',', '').split('円')[0])
        qnty = int(soup.find('input', id='lot')['value'])
        img = soup.find('div', class_='item_thumbs_inner').find('img')['src']

        item = {}
        item['itemPrice'] = price * qnty
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = 0
        item['page'] = curl
        item['mainPhoto'] = img
        item['siteName'] = 'Animate'

        return item
    
    def parseAmiAmiEng(url, item_id):
        """Получение базовой информации о лоте с магазина AmiAmi

        Args:
            url (string): ссылка на лот
            item_id (string): айди лота

        Returns:
            dict: словарь с информацией о лоте
        """

        # не робит. искать обходняк, либо тупо bs4


        '''
        
        curl = f'https://api.amiami.com/api/v1.0/item?gcode={item_id}'#&lang=jp'

        headers = WebUtils.getHeader()

        headers['x-user-key'] = 'amiami_dev'

        pprint(curl)
        session = requests.session()
        page = session.get(curl, headers=headers)
        #page = requests.get(curl, headers=headers)
        pprint(page.text)
        '''
        '''
        js = page.json()

        item = {}
        item['priceYen'] = js['item']['price']
        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = 0
        item['page'] = url
        item['mainPhoto'] = 'https://img.amiami.com'+js['item']['main_image_url']
        item['siteName'] = 'AmiAmiEng'
        item['name'] = js['item']['gname']

        return item
        '''
        return ''
