import xmltodict
import requests
import json
import os
import threading
from VkApi.VkInterface import VkApi as vk
from time import sleep
from pprint import pprint
import datetime
from bs4 import BeautifulSoup
from Logger import logger
from traceback import print_exc
from YahooApi.yahooApi import getAucInfo, getPic, getHeader, getPic
from confings.Consts import CURRENT_POSRED, MONITOR_CONF_PATH, INFO_MESSAGE_PATH

threads = []

def getStopList(tag):
    
    """ Выгрузка стоп-листа продавцов

    Returns:
        set: множество строк без повторений
    """
    
    sellerList = set()
    path = os.getcwd()+ f'/stopLists/{tag}_stop.txt'
    with open(path, 'r') as f:
        sellerList = set(f.read().split('\n'))
    
    return sellerList   
    
        
def formMess(info, tag):
    """Формирование сообщения о лоте в категории

    Args:
        info (dict): словарь с информацией о лоте
        tag (string): категория

    Returns:
        string: строка сообщения
    """
    
    tax_inc = f"(с учётом {info['tax']}% налога)" if int(info['tax'])>0 else ''
    blitz = f"\nБлиц: {info['blitz']}¥ {tax_inc}" if float(info['blitz'])>-1 else ''
    mess =f''' ===========================\n\nКатегория: #К_{tag}\n\nПродавец: #{info['seller']}\nОтзывы: ✅{info['goodRate']}/❌{info['badRate']}\n\nТекущая цена: {info['price']}¥ {tax_inc}{blitz}\n\nДоставка: {info['shipmentPrice']}\n\nКонец: {info['endTime']}\n\nСсылка Yahoo: {info['url']}\n\nСсылка посреда: {CURRENT_POSRED.format(info['id'])}
                ===========================
            '''
    
    return mess

def formSellerMess(info):
    """Формирование сообщения о лотах продавца

    Args:
        info (dict): список словарей с информацией о лотах
        tag (string): категория

    Returns:
        string: строка сообщения
    """

    mess = f''' ===========================\n\n Продавец: #{info[0]['seller']}\nОтзывы: ✅{info[0]['goodRate']}/❌{info[0]['badRate']}'''
    
    for i in range(len(info)):

        tax_inc = f"(с учётом {info[i]['tax']}% налога)" if int(info[i]['tax'])>0 else ''
        blitz = f"\nБлиц: {info[i]['blitz']}¥ {tax_inc}" if float(info[i]['blitz'])>-1 else ''
        
        mess +=f'''\n\n{i+1}. Текущая цена: {info[i]['price']}¥ {tax_inc}{blitz}\nДоставка: {info[i]['shipmentPrice']}\nКонец: {info[i]['endTime']}\nYahoo: {info[i]['url']}\nПосред: {CURRENT_POSRED.format(info[i]['id'])}'''

    mess +=  '\n\n==========================='
    
    return mess

def sendHelloMessage(params, type, is_category=False):
    """Отправка привественного сообщения

    Args:
        params (dict): словарь с информацией о потоке
        type (string): тип категории
    """
    
    info = ''
    with open(INFO_MESSAGE_PATH, 'r+', encoding='utf-8') as f:
        l = f.readlines()
        category_letter = ''
        if len(l):
            category_letter = 'К_' if is_category else ''
            info = f"\n\n❗️❗️❗️ #обновления\nНовое за {datetime.datetime.now().date()}:\n\n" + "\n".join(['🆕 '+line for line in l])
            #f.truncate(0)
    mes = f'❗️❗️❗️ #инфо\nБот по {type} #{category_letter}{params["tag"]} был перезапущен\nВозможен повтор нескольких лотов.'+info
    mes += '\n\nПо всем вопросам/багам обращайтесь к @femperox'
    
    vk.sendMes(mess = mes, users = params['rcpns'])
    

def sendMessage(items, params):
    """Отправка сообщения с подборкой продавца

    Args:
        items (list): список лотов и информацией о них
        params (dict): словарь с информацией о потоке
    """

    mes = formSellerMess(items)
    pics = [x['pic'] for x in items]
    vk.sendMes(mess = mes, users = params['rcpns'], tag = params['tag'], pic = pics)
    logger.info(f"[MESSAGE-{params['tag']}] Отправлено сообщение о лотах продавца {items[0]['seller']}")
 

def bs4Monitor(curl, params):
    """Мониторинг яху с помощью API (с использованием bs4)

    Args:
        curl (string): ссылка на категорию аукционов
        params (dict): словарь с информацией о потоке
    """

    path = os.getcwd()+'/confings/privates.json'
    tmp_dict = json.load(open(path, encoding='utf-8'))
    app_id = tmp_dict['yahoo_jp_app_id']

    seen_aucs = []
    prev_seen_aucs = []
    tmp_seen_aucs = []
    item = {}
    
    firstSeen = True # при первом запуске просматривается только 1 элемент

    sendHelloMessage(params, 'категории', is_category = True)

    while True:
        try:
            
            r = requests.get(curl)
            soup = BeautifulSoup(r.text, "html.parser")

            allLots = soup.findAll('ul', class_='Products__items')[0]
            allLots = allLots.findAll('div', class_='Product__bonus')

            notBreakSeen = True
            i = 0
            currentSize = len(allLots)
            
            if firstSeen == True:
                currentSize = 1
                allLots = allLots[:1]
                firstSeen = False
            
            for lot in allLots:

                stopSellerList = getStopList(params['tag'])

                item['id'] = lot['data-auction-id']
                if item['id'] in seen_aucs or item['id'] in prev_seen_aucs:
                    notBreakSeen = False
                    break

                tmp_seen_aucs.append(item['id'])
                i += 1
                
                item['seller'] = lot['data-auction-sellerid']
                item['price'] = float(lot['data-auction-startprice'])
                if item['seller'] in stopSellerList or item['price'] > params['maxPrice']-1:
                    continue

                info = getAucInfo(app_id, item['id'], params['tag'])

                if len(info) == 0:
                    continue
                item.update(info)
                
                if item['pic'] == '' or int(item['goodRate']) < params['minRep']:
                    continue              
                
                mes = formMess(item, params['tag'])
                vk.sendMes(mess = mes, users = params['rcpns'], tag = params['tag'], pic = [item['pic']])
                logger.info(f"[MESSAGE-{params['tag']}] Отправлено сообщение о лоте {item['id']}")
            
            if ((not notBreakSeen and i != currentSize) or (notBreakSeen and i == currentSize)) and tmp_seen_aucs:
                prev_seen_aucs = seen_aucs.copy()
                seen_aucs = tmp_seen_aucs.copy()

            tmp_seen_aucs = []
            logger.info(f"[SEEN-{params['tag']}] Просмотренные аукционы: {seen_aucs}")
            sleep(50)
        except Exception as e:
            if tmp_seen_aucs:
                prev_seen_aucs = seen_aucs.copy()
                seen_aucs = tmp_seen_aucs.copy()
            tmp_seen_aucs = []
            logger.info(f"\n[ERROR-{params['tag']}] {e}\n Последние лоты теперь: {seen_aucs}\n")
            print(f"\n{datetime.datetime.now()} - [ERROR-{params['tag']}]  Упал поток - {e}\n Последние лоты теперь: {seen_aucs}\n")

def bs4SellerMonitor(curl, params):
    """Мониторинг продавцов яху с помощью API (с использованием bs4)

    Args:
        curl (string): ссылка на аукционы продавца
        params (dict): словарь с информацией о потоке
    """

    path = os.getcwd()+'/confings/privates.json'
    tmp_dict = json.load(open(path, encoding='utf-8'))
    app_id = tmp_dict['yahoo_jp_app_id']

    seen_aucs = []
    prev_seen_aucs = []
    tmp_seen_aucs = []
    item = {}
    items = []
    pics = []
    
    firstSeen = True # при первом запуске просматривается только 1 элемент

    sendHelloMessage(params, 'продавцу')

    while True:
        try:
           
            r = requests.get(curl)
            soup = BeautifulSoup(r.text, "html.parser")

            allLots = soup.findAll('div', class_='Product__bonus')

            notBreakSeen = True
            i = 0
            currentSize = len(allLots)
            
            if firstSeen == True:
                currentSize = 1
                allLots = allLots[:1]
                firstSeen = False
            
            for lot in allLots:
                item['id'] = lot['data-auction-id']

                if item['id'] in seen_aucs or item['id'] in prev_seen_aucs:
                    notBreakSeen = False
                    break

                tmp_seen_aucs.append(item['id'])
                i += 1
                
                item['seller'] = lot['data-auction-sellerid']
                item['price'] = float(lot['data-auction-startprice'])

                info = getAucInfo(app_id, item['id'], params['tag'])

                if len(info) == 0:
                    continue
                
                item.update(info)
                
                if item['pic'] == '':
                    continue

                items.append(item.copy())
                if len(items) == 10:              
                    sendMessage(items, params)
                    items = []
            
            if ((not notBreakSeen and i != currentSize) or (notBreakSeen and i == currentSize)) and tmp_seen_aucs:
                prev_seen_aucs = seen_aucs.copy()
                seen_aucs = tmp_seen_aucs.copy()
                if len(items)> 0 and len(items) < 10:
                    sendMessage(items, params)
                    items = []
            
            tmp_seen_aucs = []
            logger.info(f"[SEEN-{params['tag']}] Просмотренные аукционы: {seen_aucs}")
            sleep(50)
        except Exception as e:
            if tmp_seen_aucs:
                prev_seen_aucs = seen_aucs.copy()
                seen_aucs = tmp_seen_aucs.copy()
            tmp_seen_aucs = []
            logger.info(f"\n[ERROR-{params['tag']}] {print_exc()}\n Последние лоты теперь: {seen_aucs}\n")
            print(f"\n{datetime.datetime.now()} - [ERROR-{params['tag']}]  Упал поток - {e}\n Последние лоты теперь: {seen_aucs}\n")
            print_exc()

if __name__ == "__main__":
    vk = vk()
    
    
    with open(MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)
       
    vkChats = threading.Thread(target=vk.monitorChats)
    vkChats.start()
    
    
    for conf in conf_list[1:]:
        if conf["type"] == "big-category": threads.append(threading.Thread(target=bs4Monitor, args=(conf["curl"], conf["params"])))
        else: 
            threads.append(threading.Thread(target=bs4SellerMonitor, args=(conf["curl"], conf["params"])))

        threads[-1].start()
    