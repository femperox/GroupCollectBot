import psycopg2
import os
import json
from pprint import pprint
from confings.Consts import DbNames, OrdersConsts
from APIs.StoresApi.ProductInfoClass import ProductInfoClass
from APIs.TrackingAPIs.TrackInfoClass import TrackInfoClass

def getConnection(connection = DbNames.database):
    """Получить подключение к базе PostgreSQL

    Returns:
        connection object: подключение к базе
    """
    
    path = os.getcwd()+'/SQLS/privates.json'
    tmp_dict = json.load(open(path, encoding='utf-8'))

    conn = psycopg2.connect(database = tmp_dict[connection],
                            host = tmp_dict["host"],
                            user = tmp_dict["user"],
                            password = tmp_dict["password"],
                            port = tmp_dict["port"])
    return conn


def addFav(item:ProductInfoClass):
    """Добавление лота в избранное

    Args:
        item (dict): словарь с базовой информацией о лоте

    Returns:
        int: результат исполнения добавления. 0 - дубль, 1 - успешно.
    """

    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT ADD_FAV({item.user}, '{item.id}', '{item.attachement}', '{item.endTime}', '{item.siteName}', '{item.page}')")
    result = cursor.fetchone()[0]
   
    conn.commit() 
    cursor.close()
    conn.close()
    return result
    
def getFav(usr_id, offset = 0):
    """ Получить список избранного пользователя 

    Args:
        usr_id (int): числовой айди пользователя
        offset (int, optional): смещение десятки. Defaults to 0.

    Returns:
        [list, int]: список из 10 лотов в избранноми со смещением и их общее количество
    """
    
    conn = getConnection()
    cursor = conn.cursor()
    
    sel = f'''SELECT * FROM FAVOURITES 
                       WHERE USER_ID={usr_id}
                       ORDER BY END_DATE
                       LIMIT 10
                       OFFSET {offset*10}
                       '''
    cursor.execute(sel)
    result = cursor.fetchall()
    
    cursor.execute(f'''SELECT COUNT(AUCTION_ID) FROM FAVOURITES
                       WHERE USER_ID={usr_id}''')
    
    totalCount = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return [result, totalCount]
    
def deleteFav(usr_id, auc_id, store_id):
    """Удаление лота из избранного пользователя

    Args:
        usr_id (int): числовой айди пользователя
        auc_id (string): айди аукциона

    Returns:
        int: результат исполнения удаления. 0 - не находится в таблице, 1 - успешно.
    """
    
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT DEL_FAV({usr_id}, '{auc_id}', '{store_id}')")
    result = cursor.fetchone()[0]
    
    conn.commit() 
    cursor.close()
    conn.close()
    
    return result
    
def getUsers():
    """Получение всех пользователей, использующих избранное

    Returns:
        list: уникальный список числовых айди пользователей
    """
    
    conn = getConnection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT DISTINCT USER_ID FROM FAVOURITES")
    result = cursor.fetchall()
    
    conn.commit() 
    cursor.close()
    conn.close()
    
    return result

def getAllFavs(usr_id):
    """Получение ВСЕГО избранного пользователя

    Args:
        usr_id (int): числовой айди пользователя

    Returns:
        list: список лотов в избранном
    """
    
    conn = getConnection()
    cursor = conn.cursor()
    
    sel = f'''SELECT * FROM FAVOURITES 
                       WHERE USER_ID={usr_id}
                       ORDER BY END_DATE
                       '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getTags(fandom):
    """Получить список уникальных пользователей для фандома

    Args:
        fandom (string): строка с фандомом

    Returns:
        list: список пользователей
    """

    conn = getConnection()
    cursor = conn.cursor() 

    cursor.execute(f'''SELECT DISTINCT USER_ID FROM TAGS
                       WHERE FANDOM='{fandom}'
                       ORDER BY USER_ID;''')
    result = cursor.fetchall()
   
    cursor.close()
    conn.close()

    return [usr[0] for usr in result]


def addTags(usr_id, fandom):
    """Добавить пользователя в список фандомов

    Args:
        usr_id (int): id пользователя
        fandom (string): строка с фандомом

    Returns:
        int: статус добавления пользователя. 1 - успешно.
    """

    conn = getConnection()
    cursor = conn.cursor() 

    cursor.execute(f"SELECT ADD_TAG({usr_id}, '{fandom}')")
    result = cursor.fetchone()[0]
   
    conn.commit() 
    cursor.close()
    conn.close()
    
    return result

def getFandoms():
    """Получить уникальный список фандомов

    Returns:
        list: список фандомов
    """

    conn = getConnection()
    cursor = conn.cursor() 

    cursor.execute(f"SELECT DISTINCT FANDOM FROM TAGS;")
    result = cursor.fetchall()
   
    cursor.close()
    conn.close()

    return [ fandom[0] for fandom in result]


def addBans(usr_id, action_type = ''):
    """_summary_

    Args:
        usr_id (int): id пользователя
        action_type (str, optional): тип нарушения. Defaults to ''.

    Returns:
        int: количество предупреждний согласно выбранному action_type
    """

    conn = getConnection()
    cursor = conn.cursor() 

    cursor.execute(f"SELECT ADD_INSERT_BAN({usr_id}, '{action_type}')")
    result = cursor.fetchone()[0]
   
    conn.commit() 
    cursor.close()
    conn.close()
    
    return result

def getCurrentParcel():
    """Получить список актуальных трек-номеров

    Returns:
        list: список трек-номеров
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()

    cursor.execute(f'''SELECT barcode, rcpnvkid, notified, tracking_type FROM  PARCEL
                       WHERE 1=1
                       AND RCPN_GOT = FALSE
                       AND operationType NOT IN ('Уничтожение', 'Временное хранение')
                       ORDER BY tracking_type;
                   ''')

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result

def setParcelNotified(barcode):
    """Установить флажок получения оповещения

    Args:
        barcode (string): трек-номер отправления
    """    

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f"""UPDATE PARCEL
                         SET notified = TRUE
                       WHERE BARCODE ='{barcode}';""")
   
    conn.commit() 
    cursor.close()
    conn.close()

def getParcelExpireDate(barcode):
    """Получить срок хранения посылки получателя

    Args:
        barcode (string): трек-номер отправления

    Returns:
        string: дата последнего срока дня хранения
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f"SELECT expiredate from parcel where barcode='{barcode}';")
    result = cursor.fetchone()[0]
   
    cursor.close()
    conn.close()
    
    return result

def getDirectParcelExpireDate(barcode):
    """Получить срок хранения посылки получателя

    Args:
        barcode (string): трек-номер отправления

    Returns:
        string: дата последнего срока дня хранения
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f"SELECT expiredate from collect_direct_recipient where barcode='{barcode}';")
    result = cursor.fetchone()[0]
   
    cursor.close()
    conn.close()
    
    return result

def insertUpdateParcel(parcelInfo:TrackInfoClass):
    """Добавить/обновить запись об отправлени

    Args:
        parcelInfo (dict): словарь с информацией об отправлении
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f'''Call ParcelInsertUpdate( '{parcelInfo.barcode}', '{parcelInfo.sndr}', '{parcelInfo.rcpn}', 
                       '{parcelInfo.destinationIndex}', '{parcelInfo.operationIndex}', '{parcelInfo.operationDate}', 
                       '{parcelInfo.operationType}', '{parcelInfo.operationAttr}', 
                       {parcelInfo.mass}, '{parcelInfo.rcpnVkId}', '{parcelInfo.trackingType}');''')

    conn.commit() 
    cursor.close()
    conn.close()

    return

def getZeroMassParcel():
    """Получить отправления с массой равной 0

    Returns:
        list: список отправлений
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f"SELECT BARCODE FROM PARCEL WHERE MASS_GR = 0;")
    result = cursor.fetchall()
   
    cursor.close()
    conn.close()

    return [res[0] for res in result]

def setParcelMass(barcode, mass):
    """Установить массу отправления

    Args:
        barcode (string): трек-номер отправления
        mass (int): масса отправления
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f'''Call ParcelUpdateMass( '{barcode}', {mass});''')

    conn.commit() 
    cursor.close()
    conn.close()

    return

def getBannedSellersInCategory(category, store_id):
    """Получить список забаненных продавцов в категории

    Args:
        category (string): категория
        store_id (string): id магазина

    Returns:
        list: список забаненных продавцов
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f"SELECT DISTINCT SELLER_ID FROM BANNED_SELLERS WHERE CATEGORY = '{category}' AND STORE_ID = '{store_id}';")
    result = cursor.fetchall()
   
    cursor.close()
    conn.close()

    return [res[0] for res in result]

def addBannedSellers(category, seller_id, store_id):
    """Добавить продавца в бан-лист

    Args:
        category (string): категория
        seller_id (string): id продавца.
        store_id (string): id магазина

    Returns:
        int: результат исполнения добавления. 0 - дубль, 1 - успешно.
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f"SELECT INSERT_BANNED_SELLER('{seller_id}', '{category}', '{store_id}')")
    result = cursor.fetchone()[0]
   
    conn.commit() 
    cursor.close()
    conn.close()
    
    return result

def IsExistBannedSeller(category, seller_id, store_id):
    """Проверка сущестования продавца в бан-листе

    Args:
        category (string): категория
        seller_id (string): id продавца.
        store_id (string): id магазина

    Returns:
        int: результат проверки существования. 0 - нет, 1 - да.
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f"SELECT IS_EXISTS_BANNED_SELLER('{seller_id}', '{category}', '{store_id}')")
    result = cursor.fetchone()[0]
   
    conn.commit() 
    cursor.close()
    conn.close()
    
    return result

def GetNotSeenProducts(items_id, type_id):
    """Сопоставление новых и увиденных товаров. Возвращает ранее не виданные

    Args:
        items_id (list of string): список id товаров
        type_id (string): тип магазина - выборки

    Returns:
        list of string: список новых товаров
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"SELECT GET_NOT_SEEN_PRODUCTS(array{items_id}, '{type_id}')")
    result = cursor.fetchone()  

    conn.commit()
    cursor.close()
    conn.close()
    
    return result[0]

def insertNewSeenProducts(items_id, type_id):
    """Добавление новых товаров в просмотренное

    Args:
        items_id (list of string): список id товаров
        type_id (string): тип магазина - выборки
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"CALL INSERT_SEEN_PRODUCTS(array{items_id}, '{type_id}')")
    
    conn.commit() 
    cursor.close()
    conn.close()

def updateCollectSelector(collectId, collectType = OrdersConsts.CollectTypes.collect, status = '', sheet_or_range = '', 
                          parcel_id = -1, topic_id = 0, comment_id = 0, status_id = -1, posred_id = ''):
    """Обновить информацию о коллекте определённого типа

    Args:
        collectType (_type_): тип коллекта
        collectNum (_type_):номер коллекта
        status (string): статус коллекта
        parcel_id (int, optional): id посылки. Defaults to -1.
        topic_id (int, optional): id обсуждения. Defaults to 0.
        comment_id (int, optional): id комментария в обсуждении. Defaults to 0.
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f''' Call CollectUpdateSelector('{collectType}', '{collectId}', '{status}', '{sheet_or_range}', {parcel_id}, {topic_id}, {comment_id}, {status_id}, '{posred_id}');''')

    conn.commit() 
    cursor.close()
    conn.close()

def setCollectCommentId(collect_id, comment_id):
    """Установить comment_id для коллекта

    Args:
        collect_id (string): id коллекта
        comment_id (int): id комментария в обсуждении
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''update collects
             set comment_id = {comment_id}
             where collect_id = '{collect_id}';'''
    cursor.execute(sel)

    conn.commit() 
    cursor.close()
    conn.close()

def deleteParticipantsCollect(collect_id):
    """Удалить всех пользователей связанных с collect_id

    Args:
        collect_id (string): id коллекта
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f''' delete from Participants_Collects where collect_id = '{collect_id}';''')

    conn.commit() 
    cursor.close()
    conn.close()

def updateSentStatusForParticipant(collect_id, user_id, collect_type = OrdersConsts.CollectTypes.collect):
    """Обновить статус доставки позиций до участника

    Args:
        collect_id (string): id заказа
        user_id (int): id пользователя
        collect_type (CollectTypes, optional): тип заказа. Defaults to CollectTypes.collect.
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f'''Call updateSentStatusForParticipant('{collect_type}', '{collect_id}', {user_id});''')

    conn.commit() 
    cursor.close()
    conn.close()

    return

def updateInsertParticipantsCollect(collect_id, user_id, items, isYstypka = False, collect_type = OrdersConsts.CollectTypes.collect):
    """Внести изменения в таблицу коллектов и участников

    Args:
        collect_id (string): id коллекта
        user_id (int): id участника
        items (string): список позиций
        isYstypka (bool, optional): как часть уступки - нужно полностью переписывать весь коллект. Defaults to False.
    """

    if isYstypka:
        deleteParticipantsCollect(collect_id = collect_id)
    
    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f''' Call ParticipantsUpdateSelector('{collect_type}', '{collect_id}', {user_id}, '{items}');''')

    conn.commit() 
    cursor.close()
    conn.close()

def getParticipantItems(user_id):
    """Получить все айтемы пользователя

    Args:
        user_id (int): id пользователя

    Returns:
        list of string: список коллектов и позиций пользователя
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"select * from get_participant_items({user_id});")
    result = cursor.fetchall()  

    cursor.close()
    conn.close()
    
    return result   

def getStoresCollectSheetId(collect_id):
    """Получить id листа закупки

    Args:
        collect_id (string): id закупки

    Returns:
        int: id листа закупки
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"select sheet_id from stores_collects where collect_id = '{collect_id}';")
    result = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return int(result)

def getCollectNamedRange(collect_id):
    """Получить именованный диапозон коллекта

    Args:
        collect_id (string): id коллетка

    Returns:
        int: именованный диапозон
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"select named_range from collects where collect_id = '{collect_id}';")
    result = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return result


def getParticipantsInStoreCollectCount(collect_id):
    """Получить количество участников закупки

    Args:
        collect_id (string): id закупки

    Returns:
        int: количество участников закупки
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"select count(*) from Participants_Stores_Collects where collect_id = '{collect_id}';")
    result = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return result

def ifParticipantInStoreCollectExist(collect_id, user_id):
    """Определить существования участника в закупке

    Args:
        collect_id (string): id закупки
        user_id (int): id участника

    Returns:
        bool: результат
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f'''select EXISTS (select user_id from participants_stores_collects 
                   where user_id = '{user_id}' and collect_id = '{collect_id}');''')
    result = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return result

def getCollectStatuses():

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"select status_name from collects_status order by status_id;")
    result = cursor.fetchall()  

    cursor.close()
    conn.close()
    
    return result

def getCollectStatusNameById(status_id):

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"select status_name from collects_status where status_id = {status_id};")
    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()
    
    return result

def getMaxCollectId(type):
    """ Получить максимальное айди коллекта, в зависимости от его типа

    Returns:
        int: id посылки
    """
    
    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()
    
    cursor.execute(f'''select max(cast(substring(collect_id, 2) as int)) from collects
                   where collect_id like '{type}%'
                   ''')
    result = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return result

def isStoreCollectIxists(collect_title):
    """Проверка существования закупки

    Args:
        collect_title (string): название закупки

    Returns:
        bool: результат
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()
    
    cursor.execute(f'''select EXISTS (select collect_id from stores_collects 
                   where collect_id = '{collect_title}');
                   ''')
    result = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return result

def getSentNamedRanges():
    """Получить список именованных диапозонов всех коллектов/инд, что были полностью разоланы. Глубина 2 месяца от текущей даты

    Returns:
        list: список именованных диапозонов
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''with sent_collects as (
                select collect_id from participants_collects
                group by 1
                HAVING BOOL_AND(is_sent) = TRUE) 
            select named_range from collects c
            right join sent_collects sc on c.collect_id = sc.collect_id
            where expiry_date > now() - INTERVAL '2' MONTH
            order by named_range;
           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return [res[0] for res in result]        

def getMaxStoreCollectId(collect_title):
    """ Получить максимальное айди закупки, в зависимости от её названия

    Returns:
        collect_title: id посылки
    """
    
    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()
    
    cursor.execute(f'''select count(collect_id) from Stores_Collects
                       where lower(collect_id) like lower('%{collect_title}%')
                   ''')
    result = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return result

def getAllCollectsInParcel(parcel_id):
    """Получить все коллекты с посылки по parcel_id

    Args:
        parcel_id (int): id посылки.

    Returns:
        list of list: записи с посылками
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT * from get_collects_in_parcel({parcel_id});

           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getCollectsByPosredId(posred_ids):

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT * from get_collects_by_posred_ids(ARRAY[{posred_ids}]);
           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getAllActivePosredCollects():
    """Получить все коллекты с posred_id

    Returns:
        list of list: записи с посылками
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT * from get_active_posred_collects();

           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getCollectsByPosredList(posred_ids_list):
    """Получить все коллекты по списку id у посреда

    Args:
        parcel_id (list[str]): список id у посреда.

    Returns:
        list of list: записи с коллетками
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT * from get_collects_by_posred_list(ARRAY[{posred_ids_list}]);

           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getEmptyPosredIdCollects():
    """Получить все коллекты (предзаказ, выкупается), у которых пустой posred_id

    Returns:
        list of list: записи с коллетками
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT * from get_empty_posred_id_collects();

           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def GetNotSeenPosredCollects(posred_ids):
    """Сопоставление новых и увиденных товаров. Возвращает ранее не виданные

    Args:
        posred_ids (list of string): список id заказов у посреда

    Returns:
        list of string: список новых товаров
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"SELECT GET_NOT_SEEN_collects_by_posred_list(array[{posred_ids}])")
    result = cursor.fetchone()  

    cursor.close()
    conn.close()
    
    return result[0]

def getCollectTopicComment(collect_id, collect_type = OrdersConsts.CollectTypes.collect):
    """Получить topic_id и comment_id коллекта по collect_id

    Args:
        collect_id (string): id коллекта

    Returns:
        list: [topic_id и comment_id]
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT * from get_collect_topic_comment('{collect_type}', '{collect_id}');
           '''
    cursor.execute(sel)
    result = cursor.fetchone() 
        
    cursor.close()
    conn.close()
    
    return result

def getRecievedActiveCollects():
    """Получить все записи с коллектами, которые на руках и не нарушен срок хранения

    Returns:
        list of list: записи с посылками
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT * from get_recieved_active_collects();
           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getOrderParticipants(collect_id, collect_type = OrdersConsts.CollectTypes.collect):
    """Получить всех участников заказа

    Returns:
        list of list: записи с посылками
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
 
    sel = f'''SELECT * from getOrderParticipants('{collect_type}', '{collect_id}');
           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result


#============================

def updateInsertDirectCollectParcel(collect_id, parcel_info:TrackInfoClass):
    """Обновить таблицу с треком прямой доставки

    Args:
        collect_id (string): id посылки
        barcode (string, optional): статус. Defaults to ''.
        parcel_info (TrackInfoClass): информация о трекинге.

    Returns:
        int: результат обновления таблицы. 0 - запись обновлена, 1 - запись добавлена
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    if parcel_info:
        sql = f'''SELECT InsertUpdateDirectRecipient('{collect_id}', '{parcel_info.barcode}', '{parcel_info.destinationIndex}', '{parcel_info.operationIndex}', '{parcel_info.operationType}', '{parcel_info.operationAttr}', cast({parcel_info.notified} as bool));'''
    else:
        sql = f'''SELECT InsertUpdateDirectRecipient('{collect_id}', '{parcel_info.barcode}', null, null, null, null, cast({parcel_info.notified} as bool));'''
    cursor.execute(sql)
    result = cursor.fetchone()[0]
   
    conn.commit() 
    cursor.close()
    conn.close()

    return result

def getAllDirectCollectParcel():
    """Получить все записи с посылками-прямыми-заказами

    Returns:
        list of list: записи с посылками
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT collect_id, barcode, notified FROM collect_direct_recipient 
              where rcpn_got = false
              ORDER BY collect_id
           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def setDirectParcelNotified(barcode):
    """Установить флажок получения оповещения

    Args:
        barcode (string): трек-номер отправления
    """    

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f"""UPDATE collect_direct_recipient
                         SET notified = TRUE
                       WHERE BARCODE ='{barcode}';""")
   
    conn.commit() 
    cursor.close()
    conn.close()

def updateInsertCollectParcel(parcel_id, status = '', topic_id = 0, comment_id = 0):
    """Обновить таблицу с посылками коллектов

    Args:
        parcel_id (int): id посылки
        status (string, optional): статус. Defaults to ''.
        topic_id (int, optional): id обсуждения. Defaults to 0.
        comment_id (int, optional): id коммента в обсуждении. Defaults to 0.

    Returns:
        int: результат обновления таблицы. 0 - запись обновлена, 1 - запись добавлена.
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f'''SELECT InsertUpdateCollectParcel({parcel_id}, '{status}', {topic_id}, {comment_id});''')
    result = cursor.fetchone()[0]
   
    conn.commit() 
    cursor.close()
    conn.close()

    return result

def getAllCollectParcels():
    """Получить все записи с посылками

    Returns:
        list of list: записи с посылками
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT * FROM COLLECT_PARCEL 
              ORDER BY PARCEL_ID
           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getCollectParcel(parcel_id):
    """Получить запись о посылке по parcel_id

    Args:
        parcel_id (int): id посылки

    Returns:
        list: запись о посылке
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    
    sel = f'''SELECT * FROM COLLECT_PARCEL 
              where PARCEL_ID = {parcel_id}
           '''
    cursor.execute(sel)
    result = cursor.fetchone() 
        
    cursor.close()
    conn.close()
    
    return result

def getMaxCollectParcelId():
    """ Получить максимальное айди посылок

    Returns:
        int: id посылки
    """
    
    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()
    
    cursor.execute('''SELECT MAX(PARCEL_ID) FROM COLLECT_PARCEL''')
    result = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return result

#============================

def getUserMenuStatus(user_id):
    """Получить статус пользователя в чате с ботом

    Args:
        user_id (int): id пользователя

    Returns:
        string: статус в чате с ботом
    """
    
    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    sql = f"""select status_value 
        from BOT_MENU_STATUS bot
        join USER_MENU_STATUS as user1
        on (BOT.STATUS_ID = USER1.STATUS_ID)
        where USER_ID = {user_id};
    """

    cursor.execute(sql)
    result = cursor.fetchone() 

    conn.commit()
    cursor.close()
    conn.close()
    
    return result[0]

def getUserMenuCountry(user_id):
    """Получить страну расчета для пользователя в чате с ботом

    Args:
        user_id (int): id пользователя

    Returns:
        string: страна расчета
    """
    
    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    sql = f"""select country 
        from USER_MENU_STATUS
        where USER_ID = {user_id};
    """

    cursor.execute(sql)
    result = cursor.fetchone() 

    cursor.close()
    conn.close()
    
    return result[0]

def getUserMenuSession(user_id):
    """Получить сессию расчета для пользователя в чате с ботом

    Args:
        user_id (int): id пользователя

    Returns:
        int: id сессии
    """
    
    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    sql = f"""select GET_USER_MENU_SESSION_ID({user_id});"""

    cursor.execute(sql)
    result = cursor.fetchone() 

    cursor.close()
    conn.close()
    
    return result[0]

def updateUserMenuStatus(user_id, status = '', country = '', session = 0):
    """Обновить статус меню бота

    Args:
        user_id (int): id пользователя
        status (string): статус меню бота
        session (int): id сессии

    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"CALL USER_MENU_STATUS_UPDATE({user_id}, '{status}', '{country}', {session})")
   
    conn.commit() 
    cursor.close()
    conn.close()


#============================

def updateInsertPublicCollectsShopsList(vk_group_id, type = '', is_active = 1, city = '', countries = '', shops = '', fandoms = ''):
    """Обновить таблицу со списком шопов/коллектов

    Args:
        vk_group_id (int): id группы
        type (string, optional): тип посредничества. Defaults to ''.
        is_active (int, optional): активность сообщества. Defaults to 1.
        city (string, city): город. Defaults to ''.
        countries (string, city): страны. Defaults to ''.
        shops (string, city): магазины. Defaults to ''.
        fandoms (string, city): фандомы. Defaults to ''.

    Returns:
        int: результат обновления таблицы. 0 - запись существует, 1 - запись добавлена.
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
    cursor.execute(f'''SELECT InsertUpdatePublicCollectsShopsList({vk_group_id}, '{type}', cast({is_active} as bool), '{city}', '{countries}', '{shops}', '{fandoms}');''')
    result = cursor.fetchone()[0]
   
    conn.commit() 
    cursor.close()
    conn.close()

    return result

def updateInsertPublicCollectsShopsAdminsList(vk_admin_id, vk_group_id, admin_role = '', is_mbo_inserted = 0):
    """Обновить таблицу со списком админов шопов/коллектов

    Args:
        vk_admin_id (int): id админа
        vk_group_id (int): id группы
        admin_role (string, optional): роль админа. Defaults to ''.
        is_mbo_inserted (int, optional): заполнение админами МБО. Defaults to 0.

    Returns:
        int: результат обновления таблицы. 0 - запись существует, 1 - запись добавлена, -1 - группы не существует.
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f'''SELECT InsertUpdatePublicCollectsShopsAdminList({vk_admin_id}, {vk_group_id}, '{admin_role}', cast({is_mbo_inserted} as bool));''')
    result = cursor.fetchone()[0]
   
    conn.commit() 
    cursor.close()
    conn.close()

    return result

def getAllCollectsShopsList(type):
    """Получить все группы шопов/коллектов по типу

    Args:
        type (string): тип посредничества.

    Returns:
        list of list: записи с группами
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
 
    sel = f'''SELECT DISTINCT vk_group_id from PUBLIC_COLLECTS_SHOPS_LIST where type = '{type}' and is_active = true;
           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getCollectsShopsList(vk_group_id):
    """Получить инфо о группе шопа/коллекта по id группы

    Args:
        vk_group_id (int): id группы.

    Returns:
        list of list: записи с инфой о группе
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
 
    sel = f'''SELECT * from PUBLIC_COLLECTS_SHOPS_LIST where vk_group_id = {vk_group_id};
           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getCollectsShopsAdminsList(vk_group_id):
    """Получить админов коллекта/шопа по id группы

    Args:
        vk_group_id (int): id группы.

    Returns:
        list of list: записи с инфой об админах группы
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
 
    sel = f'''SELECT * from PUBLIC_COLLECTS_SHOPS_ADMINS_LIST where vk_group_id = {vk_group_id};
           '''
    cursor.execute(sel)
    result = cursor.fetchall()
        
    cursor.close()
    conn.close()
    
    return result

def getRawCollectsShopsSeenRows(type):
    """_summary_

    Args:
        type (_type_): _description_

    Returns:
        _type_: _description_
    """
    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  
 
    sel = f'''SELECT next_seen_row from RAW_COLLECTS_SHOPS_SEEN_ROWS where type = '{type}';'''
    cursor.execute(sel)
    result = cursor.fetchone()
        
    cursor.close()
    conn.close()
    
    return result[0]

def UpdateRawCollectsShopsSeenRows(type, next_seen_row):
    """Обновить значение последней строки для анализа

    Args:
        type (string): тип шоп/коллект
        next_seen_row (int): новое значение
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f'''Call UpdateRawCollectsShopsSeenRows('{type}', {next_seen_row});''')

    conn.commit() 
    cursor.close()
    conn.close()

    return

def getNotSeenNews(news_ids, origin):
    """Сопоставление новых и увиденных новостей. Возвращает ранее не виданные

    Args:
        news_ids (list of string): список id новостей
        origin (string): источник

    Returns:
        list of string: список новых новостей
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"SELECT GET_NOT_SEEN_NEWS(array{news_ids}, '{origin}')")
    result = cursor.fetchone()  

    conn.commit()
    cursor.close()
    conn.close()
    
    return result[0]

def insertNewSeenNews(news_ids, origin):
    """Добавление новых новостей в просмотренное

    Args:
        news_ids (list of string): список id новостей
        origin (string): источник
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"CALL INSERT_SEEN_NEWS(array{news_ids}, '{origin}')")
    
    conn.commit() 
    cursor.close()
    conn.close()
