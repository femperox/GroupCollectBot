from APIs.GoogleSheetsApi.TagsSheet import TagsSheet as ts
from APIs.GoogleSheetsApi.CollectSheet import CollectSheet as cs
from VkApi.VkInterface import VkApi as vk
from SQLS.DB_Operations import addTags, getCurrentParcel, insertUpdateParcel, getParcelExpireDate, setParcelNotified
from Logger import logger_utils
from APIs.TrackingAPIs.TrackingSelector import TrackingSelector
from APIs.posredApi import PosredApi
from confings.Messages import Messages as mess
from confings.Consts import PochtaApiStatus, vkCoverTime, YandexTrackingApiStatus
from confings.Consts import TrackingTypes, RegexType

from pprint import pprint
import sys
from traceback import print_exc

def addNewUsers():
    """Добавить новых людей для автотегов
    """

    list = ts.getSheetListProperties()
    for usr in list:            
        usr[0] = vk.get_id(usr[0])
        

        for fandom in usr[1]:
            addTags(usr[0], fandom)
    
    ts.updateURLS(list)

def checkCollects():
    """Проверить список коллектов
    """

    collectList = cs.getSheetListProperties()

    for collect in collectList:
        if collect:
            collect[0] = vk.get_name(collect[0]).split('(')
            collect[0][0] = collect[0][0].replace('@id', '')
            collect[0][1] = collect[0][1].replace(')', '')

            collect[1] = vk.get_group_name(collect[1]).split('(')
            collect[1][0] = collect[1][0].replace('@club', '')
            collect[1][1] = collect[1][1].replace(')', '')
    
    
    cs.updateURLS(collectList)
        
    distinct_collects = set([collect[1][0] for collect in collectList])
    
    new_list = {}
    # сортировка по коллеткам
    for collect in distinct_collects:

        # cList вида - [ [ id, name, role ], ...  ]
        cList = []
        full_list = {}
        for rawCollect in collectList:
            admin_info = [rawCollect[0][0], rawCollect[0][1], rawCollect[-2]]
            if collect == rawCollect[1][0] and admin_info not in cList:
                cList.append(admin_info)
                full_list["samurai"] = rawCollect[-1]
                full_list["group_name"] = rawCollect[1][1]

            full_list["admins"] = cList.copy()

        new_list[collect] = full_list.copy()
        
    cs.createCollectView(new_list)

def updateCurrencyStatus():
    """Обновление статуса с текущим курсом рубля к йене
    """    
    try: 
        currency_rate_jpy_ami = PosredApi.getCurrentAmiCurrencyRate()
        currency_rate = PosredApi.getCurrentCurrencyRate()
        currency_rate_usd = PosredApi.getCurrentUSDCurrencyRate()
        vk.edit_group_status(mess.mes_currency.format(currency_rate_jpy_ami, currency_rate, currency_rate_usd))

        logger_utils.info(f"""[UPDATE-CURRENCY] Курс япа ~ {currency_rate_jpy_ami} и {currency_rate}; Курс США ~ {currency_rate_usd}""") 
    except Exception as e:
        logger_utils.info(f"""[ERROR-CURRENCY] {e}""")

def updateTrackingStatuses():
    """Обновление статуса посылок
    """    

    parcel_list = getCurrentParcel()

    for parcel in parcel_list:
        
        pprint(parcel)
        try:
            message = ''
            
            tracking_info = TrackingSelector.selectTracker(track = parcel[0], type = parcel[3])

            tracking_info['rcpnVkId'] = parcel[1]
            tracking_info['trackingType'] = parcel[3]

            insertUpdateParcel(tracking_info)
            if not parcel[2]:
                if parcel[3] == TrackingTypes.ids[RegexType.regex_track]:
                    if tracking_info['operationAttr'] in [PochtaApiStatus.arrived, PochtaApiStatus.notice_arrived]:
                        message = mess.mess_notify_arrival.format(tracking_info['barcode'], tracking_info['operationIndex'], getParcelExpireDate(tracking_info['barcode']))
                elif parcel[3] == TrackingTypes.ids[RegexType.regex_track_yandex]:
                    if tracking_info['operationType'] in [YandexTrackingApiStatus.arrived]:
                        message = mess.mess_notify_arrival_yandex.format(tracking_info['barcode'], tracking_info['operationAttr'], tracking_info['destinationIndex'], tracking_info['operationIndex'])

                if message:            
                    vk.sendMes(mess = message, users = tracking_info['rcpnVkId'])
                    setParcelNotified(tracking_info['barcode'])

                    logger_utils.info(f"""[NOTIFIED-TRACKING-NOTIFY] Пользователь {tracking_info['rcpnVkId']} проинфомирован об отправлении {tracking_info['barcode']}""")
            
            logger_utils.info(f"""[UPDATE-TRACKING-NOTIFY] Информация об отправлении {tracking_info['barcode']} обновлена""")
        except Exception as e:
            logger_utils.info(f"""[ERROR-TRACKING-NOTIFY] Ошибка для [{parcel[0]}] {print_exc()} : {e}""")
            pprint(e)
            continue

def updateCoverPhoto(daytime):
    """Обновление шапки сообщества

    Args:
        daytime (str): время суток
    """

    vk._cover_image_upload(image_name=vkCoverTime[daytime])

class DagLinkerValues:

    addTaggedUsers = 'addNewUsers'
    monitorCollectsList = 'checkCollects'
    updateCurrencyStatus = 'updateCurrencyStatus'
    updateTrackingStatuses = 'updateTrackingStatuses'
    updateCoverPhoto = 'updateCoverPhoto'

if __name__ == "__main__":

    vk = vk()
    ts = ts()
    cs = cs()

    pprint(sys.argv)
    if sys.argv[1] == DagLinkerValues.monitorCollectsList:
        checkCollects()
    elif sys.argv[1] == DagLinkerValues.addTaggedUsers:
        addNewUsers()
    elif sys.argv[1] == DagLinkerValues.updateCurrencyStatus:
        updateCurrencyStatus()
    elif sys.argv[1] == DagLinkerValues.updateTrackingStatuses:
        updateTrackingStatuses()
    elif sys.argv[1] == DagLinkerValues.updateCoverPhoto:
        updateCoverPhoto(sys.argv[2])