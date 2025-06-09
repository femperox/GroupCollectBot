import requests
from pprint import pprint
import json
from APIs.webUtils import WebUtils 
import time 
import gzip
from datetime import datetime
import locale


class YandexDeliveryApi():

    arrived_status = 'delivered_to_pickup_point'

    def __init__(self):

        self.driver = {}

    def startDriver(self):
        """запустить драйвер
        """
        if not self.driver:
            self.driver = WebUtils.getSelenium()

    def stopDriver(self):
        """остановить драйвер
        """
        self.driver.quit()

    def refreshDriver(self):
        """перезагрузить драйвер
        """
        self.driver.refresh()

    def getTrackingByApi(url):
        """получить информацию об отправлении по ссылке.

        Args:
            url (string): ссылка отправления

        Returns:
            dict: информация об отправлении
        """

        curl = 'https://ya-authproxy.taxi.yandex.ru/4.0/cargo-c2c/v1/shared-route/info'
        #'https://ya-authproxy.taxi.yandex.com/4.0/cargo-c2c/v1/shared-route/info'
               
        params = {'key': url.split('/')[-1]}

        headers = {
            'Accept-Language': 'ru',
            'Content-Type': 'application/json',
            'x-platform': 'web',
            'timezone': 'Europe/Moscow',
        }

        session = requests.session()
        req = session.post(url = curl, json =  params, headers=headers)
        info = req.json()

        parcel = {}
        parcel['barcode'] = url

        if 'code' in info.keys():
            parcel['operationType'] = 'delivered'
            parcel['sndr'] = ''
            parcel['rcpn'] = ''
            parcel['destinationIndex'] = ''
            parcel['operationAttr'] = ''
            parcel['operationIndex'] = ''
            parcel['operationDate'] = datetime.now()
            parcel['mass'] = 0
            return parcel

        content_sections = [content_section['items'] for content_section in info['content_sections']]
        phones = []
        for content_section in content_sections:
            phones.extend(list(filter(lambda item: 'lead_icon' in item.keys() and item['lead_icon']['image_tag'] == 'delivery_phone',  content_section)))

        parcel['sndr'] = phones[0]['subtitle']['text']
        parcel['rcpn'] = phones[1]['subtitle']['text']
        route_info = info['timeline']['bubble']['button']['action']['vertical']
        parcel['destinationIndex'] = list(filter(lambda item: item['title'] == 'Принят пунктом выдачи', route_info))[0]['subtitle']
        
        order_id = list(filter(lambda item: 'trail_text' in item.keys(),  info['content_sections'][0]['items']))
        order_id = order_id[1]['trail_text']['text'] if len(order_id) > 1 else order_id[0]['trail_text']['text']
        
        if info['summary'].lower() == 'доставлено':
            parcel['operationType'] = 'delivered'
            parcel['operationAttr'] = info['summary']
            parcel['operationIndex'] = parcel['destinationIndex']
            parcel['operationDate'] = datetime.today()
        else:
            parcel['operationType'] = info['timeline']['current_item_id']
            lastOperation = list(filter(lambda item: item['status'] == 'passed', route_info))[-1]
            parcel['operationAttr'] = order_id + ' ' + lastOperation['title'].lower()
            parcel['operationIndex'] = lastOperation['subtitle'] if 'subtitle' in lastOperation.keys() else parcel['destinationIndex']
            locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
            try:
                operationDate = datetime.strptime(lastOperation['lead_title'], '%d %b')
            except:
                operationDate = datetime.strptime(lastOperation['lead_title'], '%d %B')
            operationDate = datetime(day=operationDate.day, month=operationDate.month, year=datetime.now().year)
            parcel['operationDate'] = operationDate

        parcel['mass'] = 0
        
        return parcel

    def getTracking(self, url):
        """DEPRECATED. получить информацию об отправлении по ссылке с помощью Селениума

        Args:
            url (string): ссылка отправления

        Returns:
            dict: информация об отправлении
        """
        
        self.refreshDriver()
        self.driver.open(url)
        time.sleep(15)
        info = ''

        for request in self.driver.requests:
            if request.url.find('shared-route/info') > 0:
                info = request.response.body

        info = gzip.decompress(info)
        info = json.loads(info)

        parcel = {}
        parcel['barcode'] = url
        parcel['operationType'] = info['timeline']['current_item_id']

        if parcel['operationType'] == 'accepted':
            parcel['sndr'] = info['content_sections'][1]['items'][4]['subtitle']['text']
            parcel['rcpn'] = info['content_sections'][1]['items'][6]['subtitle']['text']
            parcel['destinationIndex'] = info['content_sections'][1]['items'][10]['subtitle']['text']
            id = info['content_sections'][1]['items'][8]['trail_payload']['buffer']
        else:
            parcel['sndr'] = info['content_sections'][0]['items'][9]['subtitle']['text']
            parcel['rcpn'] = info['content_sections'][0]['items'][11]['subtitle']['text']
            parcel['destinationIndex'] = info['content_sections'][0]['items'][3]['subtitle']['text']
            id = info['content_sections'][0]['items'][1]['trail_payload']['buffer']

        lastOperation = info['timeline']['bubble']['button']['action']['vertical']
        lastOperation = list(filter(lambda item: item['status'] == 'passed', lastOperation))[-1]
        parcel['operationAttr'] = id + ' ' + lastOperation['title'].lower()
        parcel['operationIndex'] = lastOperation['subtitle'] if 'subtitle' in lastOperation.keys() else parcel['destinationIndex']
        
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        operationDate = datetime.strptime(lastOperation['lead_title'], '%d %b')
        operationDate = datetime(day=operationDate.day, month=operationDate.month, year=datetime.now().year)
        parcel['operationDate'] = operationDate

        parcel['mass'] = 0
        
        return parcel

