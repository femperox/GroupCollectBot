import psycopg2
import os
import json
from pprint import pprint
from confings.Consts import DbNames

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


def addFav(item):
    """Добавление лота в избранное

    Args:
        item (dict): словарь с базовой информацией о лоте

    Returns:
        int: результат исполнения добавления. 0 - дубль, 1 - успешно.
    """

    conn = getConnection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT ADD_FAV({item['usr']}, '{item['id']}', '{item['attachement']}', '{item['date_end']}', '{item['store_id']}')")
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

def insertUpdateParcel(parcelInfo):
    """Добавить/обновить запись об отправлени

    Args:
        parcelInfo (dict): словарь с информацией об отправлении
    """

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor() 

    cursor.execute(f'''Call ParcelInsertUpdate( '{parcelInfo['barcode']}', '{parcelInfo['sndr']}', '{parcelInfo['rcpn']}', 
                       '{parcelInfo['destinationIndex']}', '{parcelInfo['operationIndex']}', '{parcelInfo['operationDate']}', 
                       '{parcelInfo['operationType']}', '{parcelInfo['operationAttr']}', 
                       {parcelInfo['mass']}, '{parcelInfo['rcpnVkId']}', '{parcelInfo['trackingType']}');''')


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

def getCollectId(collectType, collectNum):

    letter = "C" if collectType == "Коллективка" else "I"
    return f"{letter}{collectNum}"

def insertCollect(collectType, collectNum, namedRange):

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f'''Insert into collects values
            ('{getCollectId(collectType, collectNum)}', 0, '{namedRange}', False )
           ''')

    conn.commit() 
    cursor.close()
    conn.close()

def updateCollect(collectType, collectNum, status):

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f''' Call CollectUpdate('{getCollectId(collectType, collectNum)}', '{status}');''')

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

def updateInsertParticipantsCollect(collect_id, user_id, items, isYstypka = False):
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

    cursor.execute(f''' Call ParticipantsCollectUpdate('{collect_id}', {user_id}, '{items}');''')

    conn.commit() 
    cursor.close()
    conn.close()

def getCollectStatuses():

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f"select status_name from collects_status order by status_id;")
    result = cursor.fetchall()  

    conn.commit()
    cursor.close()
    conn.close()
    
    return result

#============================



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

def updateUserMenuStatus(user_id, status):

    conn = getConnection(DbNames.collectDatabase)
    cursor = conn.cursor()  

    cursor.execute(f''' Call USER_MENU_STATUS_UPDATE({user_id}, '{status}');''')

    conn.commit() 
    cursor.close()
    conn.close()
