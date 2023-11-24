import threading
from VkApi.VkInterface import VkApi as vk
from traceback import print_exc
from time import sleep
from JpStoresApi.AmiAmiApi import AmiAmiApi
from confings.Messages import Messages, MessageType
from confings.Consts import MonitorStoresType
from Logger import logger_stores
from APIs.webUtils import WebUtils
import random
from SQLS.DB_Operations import insertNewSeenProducts
from confings.Consts import STORE_MONITOR_CONF_PATH
import json

maxProxyTick = 25

def createItemPairs(items):
    """Сгруппировать товары в группы по 10шт

    Args:
        items (list of dict): список товаров

    Returns:
        list of list of dict: сгруппированный список товаров
    """

    items_parts = []
    message_img_limit = 10
    
    i = 0
    for i in range(0, len(items) // message_img_limit):
        items_parts.append(items[(i) * message_img_limit : (i+1)* message_img_limit])

    if len(items) % message_img_limit != 0 and len(items_parts):
        items_parts.append(items[(i+1) * message_img_limit : len(items)])
    elif len(items) % message_img_limit != 0 and i == 0:
        items_parts.append(items[(i) * message_img_limit : len(items)])    

    return items_parts

def checkNewProxies(oldProxies, oldProxyTick):
    """Обновление списка прокси

    Args:
        oldProxies (list of string): старый список прокси
        oldProxyTick (int): старое значение счётчика вызова прокси

    Returns:
        list of string: новый список прокси
        int: новое значение счётчика вызова прокси
    """

    if oldProxyTick == maxProxyTick:

        proxies = WebUtils.getProxyServer()
        sleep(2)

        return proxies, 0
    else:
        sleep(60)
        return oldProxies, oldProxyTick

def monitorAmiProduct(rcpns, typeRRS, newProxyTick):
    """Мониторинг разделов typeRRS на АмиАми

       Args:
           typeRRS (string): категория мониторинга
           newProxyTick (int): значение счётчика вызова прокси    
    """

    seen_ids = []
    proxies = []
    
    while True:

        proxies, newProxyTick = checkNewProxies(oldProxies = proxies, oldProxyTick = newProxyTick)

        if not proxies:
            newProxyTick += 1
            continue

        try:

            if typeRRS == MonitorStoresType.amiAmiEngPreOwned:
                items = AmiAmiApi.preownedAmiAmiEng(type_id = typeRRS, proxy = random.choice(proxies))
            elif typeRRS == MonitorStoresType.amiAmiEngPreOrder:
                items = AmiAmiApi.preOrderAmiAmiEng(type_id = typeRRS, proxy = random.choice(proxies))
            else:
                items = AmiAmiApi.productsAmiAmiEng(type_id = typeRRS, proxy = random.choice(proxies))
            logger_stores.info(f"[SEEN-{typeRRS}] len {len(items)} :{[x['itemId'] for x in items]}")

            if items:
                # сбор в сообщения по 10шт
                items_parts = createItemPairs(items = items)

                for part in items_parts:
                            
                    mes = Messages.formAmiAmiMess(part, typeRRS)
                    pics = [x['mainPhoto'] for x in part]
                    vk.sendMes(mess = mes, users = rcpns, tag = typeRRS, pic = pics)

                    seen_ids = [x['itemId'] for x in part]
                    logger_stores.info(f"[MESSAGE-{typeRRS}] Отправлено сообщение {seen_ids}")
                    insertNewSeenProducts(items_id=seen_ids, type_id= typeRRS)

            newProxyTick += 1

        except Exception as e:
            logger_stores.info(f"\n[ERROR-{typeRRS}] {e} - {print_exc()}\n Последние айтемы теперь: {seen_ids}\n")
            newProxyTick += 1    

     
if __name__ == "__main__":
    vk = vk()

    with open(STORE_MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)
    
    threads = []

    for conf in conf_list:

        if conf["type"] == MessageType.monitor_amiAmi.value:
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngPreOwned, maxProxyTick)))
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngSale,     maxProxyTick - 1)))
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngInStock,  maxProxyTick - 2)))
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngPreOrder, maxProxyTick - 4)))


    for thread in threads:
        thread.start()