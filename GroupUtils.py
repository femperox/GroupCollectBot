from SQLS.DB_Operations import getCurrentParcel, insertUpdateParcel
from APIs.posredApi import getCurrentCurrencyRate
from APIs.utils import getCurrentTime
from VkApi.VkInterface import VkApi as vk
from confings.Consts import HOURS_12
from Logger import logger_utils


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



try:
    vk = vk()

    threads.append(threading.Thread(target=updateCurrencyStatus))
    threads[-1].start()

except Exception as e:
    logger_utils.info(f"[ERROR_UTILS] {getCurrentTime()} {e}")   


