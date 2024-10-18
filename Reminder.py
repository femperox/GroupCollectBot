from VkApi.VkInterface import VkApi as vk
import threading
from pprint import pprint
from datetime import datetime
from time import sleep
from SQLS.DB_Operations import getUsers, getAllFavs, deleteFav
import threading
from Logger import logger_fav
from APIs.StoresApi.JpStoresApi.yahooApi import yahooApi as ya
import json
import os
from confings.Consts import CURRENT_POSRED, Stores
from confings.Messages import Messages
from APIs.StoresApi.JpStoresApi.StoreSelector import StoreSelector
from APIs.StoresApi.JpStoresApi.MercariApi import MercariApi

NOTIFY_DIFFERENCE = 10*60 + 10


threads = []

def addNotifiers():
    
    checked_users = []
    
    while True:
    
        users = [x[0] for x in getUsers()]
        for user in users:
            if user in checked_users:
                continue
            checked_users.append(user)
            threads.append(threading.Thread(target=checkTime, args=(user, )))
            threads[-1].start()
        

def checkTime(usr_id):
    yahooApi = ya()
    storesApi = StoreSelector()
    checked_lots = []
    while True:
        sleep(60) 
        allFavs = getAllFavs(usr_id)

        for fav in allFavs:
            pprint(fav)
            sleep(2)
            try:
                now = datetime.now()
     
                # Если лот уже закончился - удаляем
                if now > fav[3]:
                    deleteFav(fav[0], fav[1], fav[-2])
                    if [fav[1], fav[4]] in checked_lots: checked_lots.remove([fav[1], fav[4]])
                    logger_fav.info(f"[DELETE_FAV-{fav[0]}] для пользователя {fav[0]} был удалён лот {fav[-2]}_{fav[1]} по причине его окончания!!!")
                    continue

                item_url = storesApi.getStoreUrlByItemId( item_id = fav[1], store_type= fav[-2])
                
                # Если уже пришло оповещение - смотрим дальше
                if [fav[1], fav[4]] in checked_lots: 
                    continue                
                
                # если товар выкупил кто-то или сняли с продажи
                if fav[4] == Stores.mercari:
                    info = MercariApi.parseMercariPage(url = item_url, item_id = fav[1])
                    if info['itemStatus'] != MercariApi.MercariItemStatus.on_sale:
                        
                        deleteFav(fav[0], fav[1], fav[-2])
                        mess = Messages.formSoldOutReminderMes(vk.get_name(fav[0]), f'{fav[-2]}_{fav[1]}', item_url)
                        vk.sendMes(mess=mess, users=fav[0], pic= [fav[2]] if fav[2] else [])
                        
                        logger_fav.info(f"[NOTIFY_DELETE_FAV-{fav[0]}] для пользователя {fav[0]} отправлено уведомление о выкупе {fav[-2]}_{fav[1]}")

                elif fav[4] == Stores.yahooAuctions:            
  
                    diff = fav[3] - now
                    diff = round(diff.total_seconds())
        
                    # окончание аукциона
                    if diff <= NOTIFY_DIFFERENCE:
                        checked_lots.append([fav[1], fav[4]])
                        
                        current_price = yahooApi.getCurrentPrice(fav[1])
                        mess = Messages.formAucReminderMes(vk.get_name(fav[0]), f'{fav[-2]}_{fav[1]}', current_price, item_url)

                        vk.sendMes(mess=mess, users=fav[0], pic= [fav[2]] if fav[2] else [])
                        logger_fav.info(f"[NOTIFY_FAV-{fav[0]}] для пользователя {fav[0]} отправлено уведомление о {fav[-2]}_{fav[1]}")
            except Exception as e:
                    logger_fav.info(f"[ERROR_FAV-{fav[0]}] для пользователя {fav[0]} {e} - {fav}")
                    continue
           

try:
    vk = vk()

    threads.append(threading.Thread(target=addNotifiers))
    threads[-1].start()
except Exception as e:
    logger_fav.info(f"[ERROR_FAV] {e}")   