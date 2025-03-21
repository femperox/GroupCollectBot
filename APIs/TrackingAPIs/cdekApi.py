from datetime import datetime
import requests
from pprint import pprint
from APIs.webUtils import WebUtils
from selenium.webdriver.common.by import By
import json

class CdekApi:

    arrived_status = 'READY_FOR_PICK_UP'

    def __init__(self):

        self.driver = {}

    def startDriver(self):
        """запустить драйвер
        """
        if not self.driver:
            self.driver = WebUtils.getSelenium(isUC=True)

    def stopDriver(self):
        """остановить драйвер
        """
        self.driver.quit()

    def refreshDriver(self):
        """перезагрузить драйвер
        """
        self.driver.refresh()

    def getTracking(self, url):
        """Возвращает информационный справочник по отправлению

        Args:
            url (string): url отправления

        Returns:
            dict: информационный справочник по отправлению
        """

        barcode = url.split("/")[-1].split("=")[-1]
        curl = f'https://www.cdek.ru/api-site/track/info/?track={barcode}'
        
        self.driver.open(curl)

        info = self.driver.find_element(By.XPATH,".//pre").text
        info = json.loads(info)
        
        parcel = {}
        parcel['barcode'] = barcode
        
        parcel['sndr'] = '.'
        parcel['rcpn'] = info['data']['receiver']['initials']
        parcel['destinationIndex'] = info['data']['receiver']['address']['title'] + ', ' + info['data']['receiver']['address']['city']['name']
        parcel['mass'] = int(info['data']['weight'] * 1000)

        lastOperation = list(filter(lambda item: item['completed'] == True, info['data']['statuses']))[-1]
        if 'items' in lastOperation.keys():
            lastCity = lastOperation['items'][-1]
            lastInfo = lastCity['statuses'][-1]
            parcel['operationIndex'] = lastCity['name']
            parcel['operationDate'] = lastInfo['date']
            parcel['operationType'] = lastInfo['code']
            parcel['operationAttr'] = lastInfo['name']
        else:
            parcel['operationType'] = info['data']['status']['code']
            parcel['operationAttr'] = info['data']['status']['note']
            parcel['operationIndex'] = info['data']['cityFrom']['name']
            parcel['operationDate'] = info['data']['status']['timestamp']   

        return parcel
