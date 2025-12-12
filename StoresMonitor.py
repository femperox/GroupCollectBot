import threading
from APIs.VkApi.VkInterface import VkApi as vk
from traceback import print_exc
from time import sleep
from APIs.StoresApi.JpStoresApi.AmiAmiApi import AmiAmiApi
from confings.Messages import Messages, MessageType
from confings.Consts import OrdersConsts, PathsConsts
from Logger import logger_stores
from SQLS.DB_Operations import insertNewSeenProducts
import json
from APIs.utils import createItemPairs


def monitorAmiProduct(rcpns, typeRRS, start_sleep = 0):
    """Мониторинг разделов typeRRS на АмиАми

       Args:
           typeRRS (string): категория мониторинга  
    """

    seen_ids = []
    sleep(start_sleep)
    while True:
        try:
            
            if typeRRS == OrdersConsts.MonitorStoresType.amiAmiEngPreOwned:
                items = AmiAmiApi.preownedAmiAmiEng(type_id = typeRRS, logger = logger_stores)
            elif typeRRS == OrdersConsts.MonitorStoresType.amiAmiEngPreOrder:
                items = AmiAmiApi.preOrderAmiAmiEng(type_id = typeRRS, logger = logger_stores)
            else:
                items = AmiAmiApi.productsAmiAmiEng(type_id = typeRRS, logger = logger_stores)
            logger_stores.info(f"[SEEN-{typeRRS}] len {len(items)} :{[x.id for x in items]}")

            if items:

                # сбор в сообщения по 10шт
                items_parts = createItemPairs(items = items)

                for part in items_parts:
                    sleep(0.5)
                    mes = Messages.formAmiAmiMess(part, typeRRS)
                    pics = [x.mainPhoto for x in part]
                    vk.sendMes(mess = mes, users = rcpns, tag = typeRRS, pic = pics)

                    seen_ids = [x.id for x in part]
                    logger_stores.info(f"[MESSAGE-{typeRRS}] Отправлено сообщение {seen_ids}")
                    insertNewSeenProducts(items_id=seen_ids, type_id= typeRRS)
            
        except Exception as e:
            logger_stores.info(f"\n[ERROR-{typeRRS}] {e} - {print_exc()}\n Последние айтемы теперь: {seen_ids}\n")
            print(e)
            print(print_exc())
            sleep(360)   
            continue
        sleep(360)

if __name__ == "__main__":
    vk = vk()

    with open(PathsConsts.STORE_MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)
    
    threads = []


    for conf in conf_list[1:]:

        if conf["type"] == MessageType.monitor_amiAmi.value:
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], OrdersConsts.MonitorStoresType.amiAmiEngPreOwned)))
            threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], OrdersConsts.MonitorStoresType.amiAmiEngSale, 60)))
            #threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], OrdersConsts.MonitorStoresType.amiAmiEngPreOrder)))
            #threads.append(threading.Thread(target=monitorAmiProduct, args=( conf["rcpns"], OrdersConsts.MonitorStoresType.amiAmiEngInStock)))

    for thread in threads:
        thread.start()