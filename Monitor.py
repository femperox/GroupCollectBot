import json
import os
import threading
from VkApi.VkInterface import VkApi as vk
from traceback import print_exc
from time import sleep
from pprint import pprint
import datetime
from APIs.webUtils import WebUtils
from Logger import logger
from traceback import print_exc
from APIs.StoresApi.JpStoresApi.yahooApi import yahooApi
from APIs.StoresApi.JpStoresApi.MercariApi import MercariApi
from confings.Consts import MONITOR_CONF_PATH, PRIVATES_PATH, Stores
from confings.Messages import MessageType, Messages
from APIs.utils import getActiveMonitorChatsTypes, createItemPairs
from SQLS.DB_Operations import IsExistBannedSeller, insertNewSeenProducts
from VkApi.objects.VkButtons import VkButtons

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
    pics = [x['mainPhoto'] for x in items]
    keyboard = VkButtons.form_inline_buttons(type = MessageType.monitor_seller, items = pics)
    vk.sendMes(mess = mes, users = params['rcpns'], tag = params['tag'], pic = pics, keyboard = keyboard)
    logger.info(f"[MESSAGE-{params['tag']}] Отправлено сообщение о лотах продавца {items[0]['seller']}")
 

def bs4MonitorYahoo(curl, params):
    """Мониторинг яху с помощью API (с использованием bs4)

    Args:
        curl (string): ссылка на категорию аукционов
        params (dict): словарь с информацией о потоке
    """

    seen_aucs = []
    prev_seen_aucs = []
    tmp_seen_aucs = []
    item = {}
    
    firstSeen = True # при первом запуске просматривается только 1 элемент

    while True:
        sleep(50)

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
                item['price'] = int(lot['data-auction-startprice'])
                if IsExistBannedSeller(seller_id = item['seller'], category = params['tag'], store_id= Stores.yahooAuctions) or item['price'] > params['maxPrice']-1:
                    continue

                info = yahooApi.getAucInfo(item['id'])

                if len(info) == 0:
                    continue
                item.update(info)
                
                if item['mainPhoto'] == '' or int(item['goodRate']) < params['minRep']:
                    continue              
                
                mes = Messages.formMess(item, params['tag'])
                keyboard = VkButtons.form_inline_buttons(type = MessageType.monitor_big_category)
                vk.sendMes(mess = mes, users = params['rcpns'], tag = params['tag'], pic = [item['mainPhoto']], keyboard = keyboard )
                logger.info(f"[MESSAGE-{params['tag']}] Отправлено сообщение о лоте {item['id']}")
            
            if ((not notBreakSeen and i != currentSize) or (notBreakSeen and i == currentSize)) and tmp_seen_aucs:
                prev_seen_aucs = seen_aucs.copy()
                seen_aucs = tmp_seen_aucs.copy()

            tmp_seen_aucs = []
            logger.info(f"[SEEN-{params['tag']}] Просмотренные аукционы: {seen_aucs}")
            
        except Exception as e:
            if tmp_seen_aucs:
                prev_seen_aucs = seen_aucs.copy()
                seen_aucs = tmp_seen_aucs.copy()
            tmp_seen_aucs = []
            logger.info(f"\n[ERROR-{params['tag']}] {e}\n Последние лоты теперь: {seen_aucs}\n")
            print(f"\n{datetime.datetime.now()} - [ERROR-{params['tag']}]  Упал поток - {e} - {print_exc()}\n Последние лоты теперь: {seen_aucs}\n")
            continue

def bs4SellerMonitorYahoo(curl, params):
    """Мониторинг продавцов яху с помощью API (с использованием bs4)

    Args:
        curl (string): ссылка на аукционы продавца
        params (dict): словарь с информацией о потоке
    """
    seen_aucs = []
    prev_seen_aucs = []
    tmp_seen_aucs = []
    item = {}
    items = []
    
    firstSeen = True # при первом запуске просматривается только 1 элемент

    while True:
        sleep(50)
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

                info = yahooApi.getAucInfo(item['id'])

                if len(info) == 0:
                    continue
                
                item.update(info)
                
                if item['mainPhoto'] == '':
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

        except Exception as e:
            if tmp_seen_aucs:
                prev_seen_aucs = seen_aucs.copy()
                seen_aucs = tmp_seen_aucs.copy()
            tmp_seen_aucs = []
            logger.info(f"\n[ERROR-{params['tag']}] {print_exc()}\n Последние лоты теперь: {seen_aucs}\n")
            print(f"\n{datetime.datetime.now()} - [ERROR-{params['tag']}]  Упал поток - {e}\n Последние лоты теперь: {seen_aucs}\n")
            print_exc()
            continue

def monitorMercari(key_word, params):
    items = []

    while True:
            sleep(300)
            try:
                items = MercariApi.monitorMercariCategory(key_word = key_word, type_id = params['tag'])
                logger.info(f"[SEEN-{params['tag']}] Просмотренные аукционы: {len([x['itemId'] for x in items])}")

                if items: 
                    items_parts = createItemPairs(items = items, message_img_limit=5)

                    for part in items_parts:
                                
                        mes = Messages.formMercariMess(part, params['tag'])
                        pics = [x['mainPhoto'] for x in part]

                        keyboard = VkButtons.form_inline_buttons(type = MessageType.monitor_big_category_other, items = part)
                        vk.sendMes(mess = mes, users = params['rcpns'], tag = params['tag'], pic = pics, keyboard = keyboard)
                        

                        seen_ids = [x['itemId'] for x in part]
                        logger.info(f"[MESSAGE-{params['tag']}] Отправлено сообщение {seen_ids}")
                        insertNewSeenProducts(items_id = seen_ids, type_id = params['tag'])

            except Exception as e:
                
                logger.info(f"\n[ERROR-{params['tag']}] {e} - {print_exc()}\n Последние лоты теперь: {[x['itemId'] for x in items]}\n")
                print(f"\n{datetime.datetime.now()} - [ERROR-{params['tag']}]  Упал поток - {e} - {print_exc()}\n Последние лоты теперь: {[x['itemId'] for x in items]}\n")
                continue

if __name__ == "__main__":
    vk = vk()
    yahooApi = yahooApi()
    
    with open(MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)
          
    active_chats = []
    for conf in conf_list[1:]:
        
        if conf["store"] == Stores.yahooAuctions:
            if conf["type"] == "big-category": threads.append(threading.Thread(target=bs4MonitorYahoo, args=(conf["curl"], conf["params"])))
            else: 
                threads.append(threading.Thread(target=bs4SellerMonitorYahoo, args=(conf["curl"], conf["params"])))
        elif conf["store"] == Stores.mercari:
            threads.append(threading.Thread(target=monitorMercari, args=(conf["curl"], conf["params"])))
        
        active_chats.append(conf)

    sendHelloMessage(active_chats)

    for thread in threads:
        thread.start()
    