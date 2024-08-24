import requests
from pprint import pprint
import json
from APIs.webUtils import WebUtils 
import time 
import gzip
from datetime import datetime
import locale


class YandexDeliveryApi():

    driver = {}

    @staticmethod
    def startDriver():
        YandexDeliveryApi.driver = WebUtils.getSelenium()

    @staticmethod
    def stopDriver():
        YandexDeliveryApi.driver.quit()

    @staticmethod
    def refreshDriver():
        YandexDeliveryApi.driver.refresh()

    @staticmethod
    def getTracking(url):
        
        YandexDeliveryApi.refreshDriver()
        YandexDeliveryApi.driver.open(url)
        time.sleep(7)
        info = ''

        for request in YandexDeliveryApi.driver.requests:
            if request.url.find('shared-route/info') > 0:
                info = request.response.body

        info = gzip.decompress(info)
        info = json.loads(info)

        parcel = {}
        parcel['barcode'] = url
        parcel['sndr'] = info['content_sections'][0]['items'][9]['subtitle']['text']
        parcel['rcpn'] = info['content_sections'][0]['items'][11]['subtitle']['text']
        parcel['operationType'] = info['timeline']['current_item_id']

        id = info['content_sections'][0]['items'][1]['trail_payload']['buffer']
        lastOperation = info['timeline']['bubble']['button']['action']['vertical']
        lastOperation = list(filter(lambda item: item['status'] == 'passed', lastOperation))[-1]
        parcel['operationAttr'] = id + ' ' + lastOperation['title'].lower()
        parcel['operationIndex'] = lastOperation['subtitle']
        
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        operationDate = datetime.strptime(lastOperation['lead_title'], '%d %b')
        operationDate = datetime(day=operationDate.day, month=operationDate.month, year=datetime.now().year)
        parcel['operationDate'] = operationDate
        
        parcel['destinationIndex'] = info['content_sections'][0]['items'][3]['subtitle']['text']
        parcel['mass'] = 0
        
        return parcel

