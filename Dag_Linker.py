from APIs.GoogleSheetsApi.TagsSheet import TagsSheet as ts
from APIs.GoogleSheetsApi.CollectSheet import CollectSheet as cs
from VkApi.VkInterface import VkApi as vk
from SQLS import DB_Operations
from Logger import logger_utils
from APIs.TrackingAPIs.TrackingSelector import TrackingSelector
from APIs.posredApi import PosredApi
from confings.Messages import Messages as mess
from confings.Consts import PochtaApiStatus, vkCoverTime, YandexTrackingApiStatus
from confings.Consts import TrackingTypes, RegexType, CollectTypes
from APIs.GoogleSheetsApi.StoresCollectOrdersSheets import StoresCollectOrdersSheets
from APIs.GoogleSheetsApi.CollectOrdersSheet import CollectOrdersSheet
import time

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
            DB_Operations.addTags(usr[0], fandom)
    
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

    parcel_list = DB_Operations.getCurrentParcel()

    for parcel in parcel_list:
        
        pprint(parcel)
        try:
            message = ''
            
            tracking_info = TrackingSelector.selectTracker(track = parcel[0], type = parcel[3])

            tracking_info['rcpnVkId'] = parcel[1]
            tracking_info['trackingType'] = parcel[3]

            DB_Operations.insertUpdateParcel(tracking_info)
            if not parcel[2]:
                if parcel[3] == TrackingTypes.ids[RegexType.regex_track]:
                    if tracking_info['operationAttr'] in [PochtaApiStatus.arrived, PochtaApiStatus.notice_arrived]:
                        message = mess.mess_notify_arrival.format(tracking_info['barcode'], tracking_info['operationIndex'], getParcelExpireDate(tracking_info['barcode']))
                elif parcel[3] == TrackingTypes.ids[RegexType.regex_track_yandex]:
                    if tracking_info['operationType'] in [YandexTrackingApiStatus.arrived]:
                        message = mess.mess_notify_arrival_yandex.format(tracking_info['barcode'], tracking_info['operationAttr'], tracking_info['destinationIndex'], tracking_info['operationIndex'])

                if message:            
                    vk.sendMes(mess = message, users = tracking_info['rcpnVkId'])
                    DB_Operations.setParcelNotified(tracking_info['barcode'])

                    logger_utils.info(f"""[NOTIFIED-TRACKING-NOTIFY] Пользователь {tracking_info['rcpnVkId']} проинфомирован об отправлении {tracking_info['barcode']}""")
            
            logger_utils.info(f"""[UPDATE-TRACKING-NOTIFY] Информация об отправлении {tracking_info['barcode']} обновлена""")
        except Exception as e:
            logger_utils.info(f"""[ERROR-TRACKING-NOTIFY] Ошибка для [{parcel[0]}] {print_exc()} : {e}""")
            pprint(e)
            continue

def checkDeliveryStatusToParticipants():
    """Обновление состояния отправки позиций до участника
    """
    orderInfo = DB_Operations.getRecievedActiveCollects()
    for order in orderInfo:
        time.sleep(2.5)
        try:
            participantInfo = DB_Operations.getOrderParticipants(collect_type = order[0], collect_id = order[1])

            if participantInfo:
                if order[0] == CollectTypes.collect:
                    named_range = DB_Operations.getCollectNamedRange(collect_id = order[1])
                    local_delivery_status_list = collectOrdersSheet.checkDeliveryToParticipants(namedRange = named_range, participantList = [p[0] for p in participantInfo])
                     
                elif order[0] == CollectTypes.store:
                    list_id = DB_Operations.getStoresCollectSheetId(collect_id = order[1])
                    local_delivery_status_list = storesCollectOrdersSheets.checkDeliveryToParticipants(list_id = list_id, participantList = [p[0] for p in participantInfo])
                                
                for local_delivery_status in local_delivery_status_list:
                    if local_delivery_status['is_sent']:
                        DB_Operations.updateSentStatusForParticipant(collect_id = order[1],
                                                                    collect_type = order[0],
                                                                    user_id = local_delivery_status['user'])
                        logger_utils.info(f"""[UPDATED-DELIVERY-PARTICIPANT-STATUS] Позиции пользователя {local_delivery_status['user']} для заказа [{order[1]}] отправлены""")
        
        except Exception as e:
            logger_utils.info(f"""[ERROR-DELIVERY-PARTICIPANT-STATUS] Ошибка для заказа [{order[1]}] {print_exc()} : {e}""")
            pprint(e)        

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
    checkDeliveryStatusToParticipants = 'checkDeliveryStatusToParticipants'

if __name__ == "__main__":

    vk = vk()
    ts = ts()
    cs = cs()
    collectOrdersSheet = CollectOrdersSheet()
    storesCollectOrdersSheets = StoresCollectOrdersSheets()

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
    elif sys.argv[1] == DagLinkerValues.checkDeliveryStatusToParticipants:
        checkDeliveryStatusToParticipants()