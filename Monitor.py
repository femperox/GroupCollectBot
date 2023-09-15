import json
import os
import threading
from VkApi.VkInterface import VkApi as vk
from time import sleep
from pprint import pprint
import datetime
from APIs.webUtils import WebUtils
from Logger import logger
from traceback import print_exc
from JpStoresApi.yahooApi import getAucInfo
from confings.Consts import MONITOR_CONF_PATH, PRIVATES_PATH
from confings.Messages import MessageType, Messages
from APIs.utils import getActiveMonitorChatsTypes
from SQLS.DB_Operations import IsExistBannedSeller

threads = []
        
def sendHelloMessage(active_chats):
    """Отправка привественного сообщения

    Args:
        params (dict): словарь с информацией о потоке
        type (string): тип категории
    """
    
    active_chats_info = getActiveMonitorChatsTypes(active_chats)
    for active_chat in active_chats_info:
        mes = Messages.mes_hello(active_chats_info[active_chat])    
        vk.sendMes(mess = mes, users = active_chat)
    

def sendMessage(items, params):
    """Отправка сообщения с подборкой продавца

    Args:
        items (list): список лотов и информацией о них
        params (dict): словарь с информацией о потоке
    """

    mes = Messages.formSellerMess(items)
    pics = [x['pic'] for x in items]
    vk.sendMes(mess = mes, users = params['rcpns'], tag = params['tag'], pic = pics)
    logger.info(f"[MESSAGE-{params['tag']}] Отправлено сообщение о лотах продавца {items[0]['seller']}")
 

def bs4Monitor(curl, params):
    """Мониторинг яху с помощью API (с использованием bs4)

    Args:
        curl (string): ссылка на категорию аукционов
        params (dict): словарь с информацией о потоке
    """

    tmp_dict = json.load(open(PRIVATES_PATH, encoding='utf-8'))
    app_id = tmp_dict['yahoo_jp_app_id']

    seen_aucs = []
    prev_seen_aucs = []
    tmp_seen_aucs = []
    item = {}
    
    firstSeen = True # при первом запуске просматривается только 1 элемент

    while True:
        try:
            
            soup = WebUtils.getSoup(curl, parser= WebUtils.Bs4Parsers.htmlParser)

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

                item['id'] = lot['data-auction-id']
                if item['id'] in seen_aucs or item['id'] in prev_seen_aucs:
                    notBreakSeen = False
                    break

                tmp_seen_aucs.append(item['id'])
                i += 1
                
                item['seller'] = lot['data-auction-sellerid']
                item['price'] = float(lot['data-auction-startprice'])
                if IsExistBannedSeller(seller_id = item['seller'], category = params['tag']) or item['price'] > params['maxPrice']-1:
                    continue

                info = getAucInfo(app_id, item['id'])

                if len(info) == 0:
                    continue
                item.update(info)
                
                if item['pic'] == '' or int(item['goodRate']) < params['minRep']:
                    continue              
                
                mes = Messages.formMess(item, params['tag'])
                vk.sendMes(mess = mes, users = params['rcpns'], tag = params['tag'], pic = [item['pic']], type = MessageType.monitor_big_category)
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

    tmp_dict = json.load(open(PRIVATES_PATH, encoding='utf-8'))
    app_id = tmp_dict['yahoo_jp_app_id']

    seen_aucs = []
    prev_seen_aucs = []
    tmp_seen_aucs = []
    item = {}
    items = []
    
    firstSeen = True # при первом запуске просматривается только 1 элемент

    while True:
        try:
           
            soup = WebUtils.getSoup(curl, parser= WebUtils.Bs4Parsers.htmlParser)

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

                info = getAucInfo(app_id, item['id'])

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
          
    active_chats = []

    for conf in conf_list[1:]:
        if conf["type"] == "big-category": threads.append(threading.Thread(target=bs4Monitor, args=(conf["curl"], conf["params"])))
        else: 
            threads.append(threading.Thread(target=bs4SellerMonitor, args=(conf["curl"], conf["params"])))
        active_chats.append(conf)

    sendHelloMessage(active_chats)

    for thread in threads:
        thread.start()
    