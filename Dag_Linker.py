from APIs.GoogleSheetsApi.TagsSheet import TagsSheet as ts
from APIs.GoogleSheetsApi.CollectSheet import CollectSheet as cs
from APIs.VkApi.VkInterface import VkApi as vk
from SQLS import DB_Operations
from Logger import logger_utils
from APIs.TrackingAPIs.TrackingSelector import TrackingSelector, TrackingTypes
from APIs.posredApi import PosredApi
from confings.Messages import Messages as mess
from confings.Consts import vkCoverTime, MBO_INSERTED_INFO_ID
from confings.Consts import RegexType, CollectTypes
from APIs.GoogleSheetsApi.StoresCollectOrdersSheets import StoresCollectOrdersSheets
from APIs.GoogleSheetsApi.CollectOrdersSheet import CollectOrdersSheet
import time
from APIs.GoogleSheetsApi.CollectSheet import CollectSheet
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
    """Проверить список коллектов/шопов
    """
    def checkCollectsWrapper(type, rawSheetIdKey: CollectSheet.SheetIdClass, publicSheetIdKey: CollectSheet.SheetIdClass):
        """Обертка checkCollects

        Args:
            type (string): шоп/коллект
            rawSheetIdKey (CollectSheet.SheetIdClass): ключ от листа с сырыми данными
            publicSheetIdKey (CollectSheet.SheetIdClass): ключ от листа с обработанными данными
        """
        start_row = DB_Operations.getRawCollectsShopsSeenRows(type = type)
        info = collects.getSheetListProperties(spId = collects.getSheetId(sheet_id_key = rawSheetIdKey), startRow = start_row)
        next_seen_row = info['nextSeenRow']
        info = info['collectList']

        if info:
            for inf in info:
                current_gr_id = vk.get_group_id(id = inf['group_id'].replace('club', '').split('?')[0])
                if current_gr_id in DB_Operations.getAllCollectsShopsList(type):
                    continue
                else:
                    DB_Operations.updateInsertPublicCollectsShopsList(vk_group_id = current_gr_id,
                                                        type = type,
                                                        city = inf['city'],
                                                        countries = inf['countries'],
                                                        shops = inf['shops'],
                                                        fandoms = inf['fandoms'])   
                    if inf['admin_id'] == MBO_INSERTED_INFO_ID:
                        vk_admin_id = inf['admin_id']
                        is_mbo_inserted = 1
                        admin_role = 'Заполнено МБО'          
                    else:
                        vk_admin_id = vk.get_id(inf['admin_id'])
                        is_mbo_inserted = 0
                        admin_role = inf['admin_role']

                    DB_Operations.updateInsertPublicCollectsShopsAdminsList(vk_admin_id = vk_admin_id,
                                                            vk_group_id = current_gr_id,
                                                            admin_role = admin_role,
                                                            is_mbo_inserted = is_mbo_inserted
                                                            )
                    
            collectList = DB_Operations.getAllCollectsShopsList(type = type)
            if collectList:
                formatedList = []
                for collect in collectList:
                    info = {}
                    adminsList = DB_Operations.getCollectsShopsAdminsList(vk_group_id = collect[0])
                    groupInfo = DB_Operations.getCollectsShopsList(vk_group_id = collect[0])[0]
                    groupInfoVk = vk.get_group_info(id = collect[0])['groups'][0]
                    info['groupId'] = groupInfoVk['id']
                    info['pictureUrl'] = groupInfoVk['photo_200']
                    info['groupName'] = groupInfoVk['name']
                    info['groupInfo'] = {
                        'city': groupInfo[3],
                        'countries': groupInfo[4],
                        'shops': groupInfo[5],
                        'fandoms': groupInfo[6]
                    }.copy()
                    info['admins'] = []
                    for admin in adminsList:
                        adminInfo = {}
                        adminInfo['adminId'] = admin[0]
                        adminInfo['adminRole'] = admin[2]
                        adminInfo['adminName'] = '' if admin[3] else vk.get_name(id = admin[0]).split('(')[-1].replace(')', '')
                        info['admins'].append(adminInfo.copy())
                    formatedList.append(info.copy())
                    time.sleep(2)

                formatedList.sort(key = lambda x:x['groupName'].lower())
                publicCollectList = CollectSheet(spreadsheetKey = CollectSheet.SpreadsheetKeyClass.publicShopsCollectsList)
                publicCollectList.createCollectView(collectList = formatedList, spId = collects.getSheetId(sheet_id_key = publicSheetIdKey))
                DB_Operations.UpdateRawCollectsShopsSeenRows(type = type, next_seen_row = next_seen_row)
    
    collects = CollectSheet(spreadsheetKey = CollectSheet.SpreadsheetKeyClass.rawShopsCollectsList)
    checkCollectsWrapper(type = 'коллект', 
                         rawSheetIdKey = CollectSheet.SheetIdClass.rawCollectsSheetId,
                         publicSheetIdKey = CollectSheet.SheetIdClass.publicCollectsSheetId)
    checkCollectsWrapper(type = 'шоп', 
                            rawSheetIdKey = CollectSheet.SheetIdClass.rawShopsSheetId,
                            publicSheetIdKey = CollectSheet.SheetIdClass.publicShopsSheetId)

def updateCurrencyStatus():
    """Обновление статуса с текущим курсом рубля к йене
    """    
    try: 
        currency_rate = PosredApi.getCurrentCurrencyRate()
        currency_rate_usd = PosredApi.getCurrentUSDCurrencyRate()
        vk.edit_group_status(mess.mes_currency.format(currency_rate, currency_rate_usd))

        logger_utils.info(f"""[UPDATE-CURRENCY] Курс япа ~ {currency_rate}; Курс США ~ {currency_rate_usd}""") 
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
                if parcel[3] == TrackingTypes.ids[RegexType.regex_track] and tracking_info['operationAttr'] in TrackingSelector.selectArrivedStatuses(parcel[3]):
                        message = mess.mess_notify_arrival.format(tracking_info['barcode'], tracking_info['operationIndex'], DB_Operations.getParcelExpireDate(tracking_info['barcode']))
                elif parcel[3] == TrackingTypes.ids[RegexType.regex_track_yandex] and tracking_info['operationType'] in TrackingSelector.selectArrivedStatuses(parcel[3]):
                        message = mess.mess_notify_arrival_yandex.format(tracking_info['barcode'], tracking_info['operationAttr'], tracking_info['destinationIndex'], DB_Operations.getParcelExpireDate(tracking_info['barcode']))
                elif parcel[3] == TrackingTypes.ids[RegexType.regex_track_cdek] and tracking_info['operationType'] in TrackingSelector.selectArrivedStatuses(parcel[3]):
                        message = mess.mess_notify_arrival_cdek.format(tracking_info['barcode'], tracking_info['destinationIndex'], DB_Operations.getParcelExpireDate(tracking_info['barcode']))
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

            isAllParicipantsSent = lambda arr: all(item[1] for item in arr)

            if not isAllParicipantsSent(participantInfo):
                pprint(f'Чекаем {order}')

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