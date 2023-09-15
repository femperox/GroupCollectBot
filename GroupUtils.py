from SQLS.DB_Operations import getCurrentParcel, insertUpdateParcel, getParcelExpireDate, setParcelNotified
from APIs.pochtaApi import getTracking
from APIs.posredApi import getCurrentCurrencyRate
from VkApi.VkInterface import VkApi as vk
from confings.Messages import Messages as mess
from confings.Consts import HOURS_12, HOURS_24, PochtaApiStatus
from Logger import logger_utils

from traceback import print_exc
from pprint import pprint
from time import sleep
import threading

threads = []

def updateCurrencyStatus():
    """Обновление статуса с текущим курсом рубля к йене
    """    
    
    while True:
        try: 
            currency_rate = getCurrentCurrencyRate()
            vk.edit_group_status(mess.mes_currency.format(currency_rate))

            logger_utils.info(f"""[UPDATE-CURRENCY] Курс = {currency_rate}""")
            sleep(HOURS_12)
        
        except Exception as e:

            logger_utils.info(f"""[ERROR-CURRENCY] {e}""")

def updateTrackingStatuses():
    """Обновление статуса посылок
    """    

    while True:
        try:
            parcel_list = getCurrentParcel()
            
            for parcel in parcel_list:
                tracking_info = getTracking(parcel[0])
                tracking_info['rcpnVkId'] = parcel[1]

                insertUpdateParcel(tracking_info)

                if tracking_info['operationAttr'] == PochtaApiStatus.arrived and not parcel[2]:
                    
                    message = mess.mess_notify_arrival.format(tracking_info['barcode'], tracking_info['operationIndex'], getParcelExpireDate(tracking_info['barcode']))
                    
                    vk.sendMes(mess = message, users = tracking_info['rcpnVkId'])
                    setParcelNotified(tracking_info['barcode'])

                    logger_utils.info(f"""[NOTIFIED-TRACKING-NOTIFY] Пользователь {tracking_info['rcpnVkId']} проинфомирован об отправлении {tracking_info['barcode']}""")

                
                logger_utils.info(f"""[UPDATE-TRACKING-NOTIFY] Информация об отправлении {tracking_info['barcode']} обновлена""")
            
            sleep(HOURS_24)

        except Exception as e:
            logger_utils.info(f"""[ERROR-TRACKING-NOTIFY] {print_exc()}""")
            

try:
    vk = vk()

    vkWall = threading.Thread(target=vk.monitorGroupActivity)
    vkWall.start()

    '''
    threads.append(threading.Thread(target=updateCurrencyStatus))
    threads[-1].start()

    threads.append(threading.Thread(target=updateTrackingStatuses))
    threads[-1].start()
    '''
    
except Exception as e:
    logger_utils.info(f"[ERROR_UTILS] {e}")   


