import requests
from pprint import pprint
import json
from APIs.webUtils import WebUtils 
import time 
import gzip
from datetime import datetime
import locale


class YandexDeliveryApi():

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

    def getTracking(self, url):
        """получить информацию об отправлении по ссылке

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

