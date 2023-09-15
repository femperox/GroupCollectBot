from VkApi.VkInterface import VkApi as vk
import threading
from pprint import pprint
from datetime import datetime
from time import sleep
from SQLS.DB_Operations import getUsers, getAllFavs, deleteFav
import threading
from Logger import logger_fav
from JpStoresApi.yahooApi import getCurrentPrice
import json
import os
from confings.Consts import CURRENT_POSRED

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
    
    checked_lots = []
    while True:
        
        allFavs = getAllFavs(usr_id)

        for fav in allFavs:
            try:
                now = datetime.now()
                                
                # Если лот уже закончился - удаляем 
                if now > fav[-1]:
                    deleteFav(fav[0], fav[1])
                    if fav[1] in checked_lots: checked_lots.remove(fav[1])
                    logger_fav.info(f"[DELETE_FAV-{fav[0]}] для пользователя {fav[0]} был удалён лот {fav[1]} по причине его окончания!!!")
                    continue
                            
                # Если уже пришло оповещение - смотрим дальше
                if fav[1] in checked_lots: continue
                
                diff = fav[-1] - now
                diff = round(diff.total_seconds())
     
                if diff <= NOTIFY_DIFFERENCE:
                    checked_lots.append(fav[1])
                    
                    path = os.getcwd()+'/confings/privates.json'
                    tmp_dict = json.load(open(path, encoding='utf-8'))

                    current_price = getCurrentPrice(tmp_dict["yahoo_jp_app_id"], fav[1])
                    
                    mess = f"#Уведомление для {vk.get_name(fav[0])}\n\nЛот #{fav[1]} закончится через 10 минут!\nТекущая цена: {current_price}\n\n{CURRENT_POSRED.format(fav[1])}"
                    vk.sendMes(mess=mess, users=fav[0], pic= [fav[2]])
                    logger_fav.info(f"[NOTIFY_FAV-{fav[0]}] для пользователя {fav[0]} отправлено уведомление о {fav[1]}")
            except Exception as e:
                    logger_fav.info(f"[ERROR_FAV-{fav[0]}] для пользователя {fav[0]} {e}")
        sleep(60)    

try:
    vk = vk()

    threads.append(threading.Thread(target=addNotifiers))
    threads[-1].start()
except Exception as e:
    logger_fav.info(f"[ERROR_FAV] {e}")   