from suds.client import Client
from confings.Consts import PRIVATES_PATH
import os
import json

def getClient():
    """Получение suds-клиента для работы с API ПР

    Returns:
        Client: suds-клиент
    """

    url = 'https://tracking.russianpost.ru/rtm34?wsdl'
    client = Client(url, headers={'Content-Type': 'application/soap+xml; charset=UTF-8'},
                         location='https://tracking.russianpost.ru/rtm34/')

    return client


def createMess(barcode):
    """Сформировать строку запроса к апи почты РФ

    Args:
        barcode (string): трек-номер

    Returns:
        string: сформированная строка запроса
    """    

    
    tmp_dict = json.load(open(PRIVATES_PATH, encoding='utf-8'))
    login = tmp_dict['pochta_API_usr']
    psw = tmp_dict['pochta_API_psw']

    message = \
        """<?xml version="1.0" encoding="UTF-8"?>
                        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:oper="http://russianpost.org/operationhistory" xmlns:data="http://russianpost.org/operationhistory/data" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
                        <soap:Header/>
                        <soap:Body>
                           <oper:getOperationHistory>
                              <data:OperationHistoryRequest>
                                 <data:Barcode>""" + barcode + """</data:Barcode>  
                                    <data:MessageType>0</data:MessageType>
                                    <data:Language>RUS</data:Language>
                                 </data:OperationHistoryRequest>
                                 <data:AuthorizationHeader soapenv:mustUnderstand="1">
                                    <data:login>""" + login + """</data:login>
                                <data:password>""" + psw + """</data:password>
                             </data:AuthorizationHeader>
                          </oper:getOperationHistory>
                       </soap:Body>
                    </soap:Envelope>"""

    return message


def getTracking(barcode):
    """Возвращает информационный справочник по отправлению

    Args:
        barcode (string): трек-номер

    Returns:
        dict: информационный справочник по отправлению
    """

    result = getClient().service.getOperationHistory(__inject={'msg':createMess(barcode).encode()})

    current_stat = result[0][-1]

    parcel = {}
    parcel['barcode'] = barcode
    parcel['sndr'] = current_stat['UserParameters']['Sndr']
    parcel['rcpn'] = current_stat['UserParameters']['Rcpn']

    try:
        parcel['destinationIndex'] = current_stat['AddressParameters']['DestinationAddress']['Index']
    except:
        parcel['destinationIndex'] = -1

    try:
        parcel['operationIndex'] = current_stat['AddressParameters']['OperationAddress']['Index']
    except:
        parcel['operationIndex'] = -1

    parcel['operationDate'] = current_stat['OperationParameters']['OperDate']
    parcel['operationType'] = current_stat['OperationParameters']['OperType']['Name']

    try:
        parcel['operationAttr'] = current_stat['OperationParameters']['OperAttr']['Name']
    except:
        parcel['operationAttr'] = 'none'

    try:
        parcel['mass'] = current_stat['ItemParameters']['Mass']
    except:
        parcel['mass'] = 0

    return parcel

def getMass(barcode):
    """Получить массу отправления

    Args:
        barcode (string): трек-номер

    Returns:
        int: масса отправления
    """

    result = getClient().service.getOperationHistory(__inject={'msg':createMess(barcode).encode()})

    current_stat = result[0][1]
    mass = current_stat['ItemParameters']['Mass']

    return int(mass)