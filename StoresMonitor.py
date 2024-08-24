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
from JpStoresApi.HPoiApi import HPoiApi

maxProxyTick = 10
firstStart = [True, True, True]

def refreshSessions(ticks, thread_index):
    """Обновление браузера

    Args:
        ticks (int): значение счётчика вызова

    Returns:
        int: новое значение счётчика вызова 
    """

    if ticks == maxProxyTick:
        if not firstStart[thread_index]:
            AmiAmiApi.stopDriver(thread_index)
        AmiAmiApi.startDriver(thread_index)
        logger_stores.info(f"[DRIVER] RELOAD DRIVER")
        return 0
    else:
        AmiAmiApi.refreshDriver(thread_index)
        logger_stores.info(f"[DRIVER] REFRESH PAGE")
        return ticks

def monitorAmiProduct(rcpns, typeRRS, newProxyTick, thread_index):
    """Мониторинг разделов typeRRS на АмиАми

       Args:
           typeRRS (string): категория мониторинга
           newProxyTick (int): значение счётчика вызова прокси    
    """

    seen_ids = []
    
    while True:
        
        try:

            newProxyTick = refreshSessions(ticks = newProxyTick, thread_index = thread_index )
            firstStart[thread_index] = False
            
            if typeRRS == MonitorStoresType.amiAmiEngPreOwned:
                items = AmiAmiApi.preownedAmiAmiEng(type_id = typeRRS, logger = logger_stores, thread_index = thread_index)
            elif typeRRS == MonitorStoresType.amiAmiEngPreOrder:
                items = AmiAmiApi.preOrderAmiAmiEng(type_id = typeRRS, logger = logger_stores, thread_index = thread_index)
            else:
                items = AmiAmiApi.productsAmiAmiEng(type_id = typeRRS, logger = logger_stores, thread_index = thread_index)
            logger_stores.info(f"[SEEN-{typeRRS}] len {len(items)} :{[x['itemId'] for x in items]}")

            if items:

                # сбор в сообщения по 10шт
                items_parts = createItemPairs(items = items)

                for part in items_parts:
                    sleep(0.5)
                    mes = Messages.formAmiAmiMess(part, typeRRS)
                    pics = [x['mainPhoto'] for x in part]
                    vk.sendMes(mess = mes, users = rcpns, tag = typeRRS, pic = pics)

                    seen_ids = [x['itemId'] for x in part]
                    logger_stores.info(f"[MESSAGE-{typeRRS}] Отправлено сообщение {seen_ids}")
                    insertNewSeenProducts(items_id=seen_ids, type_id= typeRRS)

            newProxyTick += 1
            
        except Exception as e:
            logger_stores.info(f"\n[ERROR-{typeRRS}] {e} - {print_exc()}\n Последние айтемы теперь: {seen_ids}\n")
            print(e)
            print(print_exc())
            newProxyTick += 1 
            sleep(360)   
            continue
        sleep(360)
        
def monitor_hpoi(rcpns, typeRRS, vk):

    seen_ids = []
    
    while True:
        
        try:

            items = HPoiApi.getHpoiTeasers(type_id = typeRRS)

            logger_stores.info(f"[SEEN-{typeRRS}] len {len(items)} :{[x['itemId'] for x in items]}")

            if items:

                # сбор в сообщения по 1шт
                items_parts = createItemPairs(items = items, message_img_limit=1)

                for part in items_parts:
                    sleep(10)
                    mes = Messages.formHpoiMess(part, typeRRS)
                    pics = [x for x in part[0]['mainPhoto']]
                    vk.sendMes(mess = mes, users = rcpns, tag = typeRRS, pic = pics)

                    seen_ids = [f"{x['itemId']}" for x in part]
                    logger_stores.info(f"[MESSAGE-{typeRRS}] Отправлено сообщение {seen_ids}")
                    insertNewSeenProducts(items_id=seen_ids, type_id= typeRRS)


        except Exception as e:
            print(e)
            logger_stores.info(f"\n[ERROR-{typeRRS}] {e} - {print_exc()}\n Последние айтемы теперь: {seen_ids}\n")    
            continue    

        sleep(10800)


if __name__ == "__main__":
    vk = vk()

    with open(STORE_MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)
    
    threads = []


    for conf in conf_list[1:]:

        if conf["type"] == MessageType.monitor_amiAmi.value:
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngPreOwned, maxProxyTick, 0)))
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngSale,     maxProxyTick-1, 1)))
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngPreOrder, maxProxyTick - 2, 2)))
            #threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], MonitorStoresType.amiAmiEngInStock,  maxProxyTick - 2)))



    for thread in threads:
        thread.start()