from SQLS.DB_Operations import getCurrentParcel, insertUpdateParcel, getParcelVkRcpn, getParcelExpireDate
from APIs.pochtaApi import getTracking
from APIs.posredApi import getCurrentCurrencyRate
from APIs.utils import getCurrentTime
from VkApi.VkInterface import VkApi as vk
from confings.Consts import HOURS_12, PochtaApiStatus
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
            mess = f'Яху ауки/Вторички/Магазины - {currency_rate}'
            vk.edit_group_status(mess)

            logger_utils.info(f"""[UPDATE-CURRENCY] Курс на {getCurrentTime()} = {currency_rate}""")
            sleep(HOURS_12)
        
        except Exception as e:

            logger_utils.info(f"""[ERROR-CURRENCY] {getCurrentTime()} {e}""")

def updateTrackingStatuses():

    try:
        parcel_list = getCurrentParcel()
        pprint(parcel_list)

        for parcel in parcel_list:
            tracking_info = getTracking(parcel)
            tracking_info['rcpnVkId'] = getParcelVkRcpn(tracking_info['barcode'])
            if tracking_info['operationAttr'] == PochtaApiStatus.arrived:
                
                mess = f"""Добрый день!\n
                           Ваша посылка с треком {tracking_info['barcode']} прибыла в отделение {tracking_info['operationIndex']}.\n
                           Не забудьте забрать её до {getParcelExpireDate(tracking_info['barcode'])} (включительно).\n\n
                           Если индекс отделения отличается от того, что вы указывали, то возможно почта РФ совершила переадресацию отправления.
                        """
                
                vk.sendMes(mess = mess, users = tracking_info['rcpnVkId'])
            insertUpdateParcel(tracking_info)

    except Exception as e:
        pprint(e)
        print_exc()

try:
    vk = vk()
    updateTrackingStatuses()
    '''
    threads.append(threading.Thread(target=updateCurrencyStatus))
    threads[-1].start()
    '''
except Exception as e:
    logger_utils.info(f"[ERROR_UTILS] {getCurrentTime()} {e}")   


