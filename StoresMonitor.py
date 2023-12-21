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
from APIs.utils import createItemPairs

maxProxyTick = 80

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

        proxies = WebUtils.getProxyServerNoSelenium(type_needed = ['socks4', 'socks5', 'http'])

        return proxies, 0
    else:
        
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
        #sleep(120)
        proxies, newProxyTick = checkNewProxies(oldProxies = proxies, oldProxyTick = newProxyTick)

        if not proxies:
            newProxyTick += 1
            continue

        if not newProxyTick:
            logger_stores.info(f"[PROXY-{typeRRS}] len {len(proxies)}")

        try:

            if typeRRS == MonitorStoresType.amiAmiEngPreOwned:
                items = AmiAmiApi.preownedAmiAmiEng(type_id = typeRRS, proxy = random.choice(proxies), logger = logger_stores)
            elif typeRRS == MonitorStoresType.amiAmiEngPreOrder:
                items = AmiAmiApi.preOrderAmiAmiEng(type_id = typeRRS, proxy = random.choice(proxies), logger = logger_stores)
            else:
                items = AmiAmiApi.productsAmiAmiEng(type_id = typeRRS, proxy = random.choice(proxies), logger = logger_stores)
            logger_stores.info(f"[SEEN-{typeRRS}] len {len(items)} :{[x['itemId'] for x in items]}")

            if items:

                # сбор в сообщения по 10шт
                items_parts = createItemPairs(items = items)

                for part in items_parts:
                    sleep(0.2)
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
            continue

     
if __name__ == "__main__":
    vk = vk()

    with open(STORE_MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)
    
    threads = []

    for conf in conf_list[1:]:

        if conf["type"] == MessageType.monitor_amiAmi.value:
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngPreOwned, maxProxyTick)))
            #threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngSale,     maxProxyTick - 1)))
            #threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngInStock,  maxProxyTick - 2)))
            #threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngPreOrder, maxProxyTick - 4)))


    for thread in threads:
        thread.start()