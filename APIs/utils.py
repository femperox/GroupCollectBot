from datetime import datetime
import os
import json
from confings.Consts import MONITOR_CONF_PATH, RegexType, STORE_MONITOR_CONF_PATH, CURRENT_POSRED
import re
from itertools import chain
from pprint import pprint
from APIs.StoresApi.JpStoresApi.StoreSelector import StoreSelector
from confings.Consts import Stores
from dateutil.relativedelta import relativedelta
import locale

def getChar(char, step):
    """Получить след символ

    Args:
        char (char): символ
        step (int): отступ от текущего символа

    Returns:
        char: след символ   
    """
    return chr(ord(char) + step)

def getCurrentDate():
    """Получить текущую дату

    Returns:
        string: текущая дата
    """
    
    return datetime.now().strftime('%Y-%m-%d')

def getCurrentMonthString():
    """Получить текущий месяц на русском языке

    Returns:
        string: текущий месяц на русском языке
    """

    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    month = datetime.strftime(datetime.now(), '%b %Y')
    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    return month

def getExpiryDateString():
    """Получить строчку срока хранения

    Returns:
        string: срок хранения
    """

    now = datetime.now()
    gotDate = now.strftime("%d.%m.%Y")
    takeDate = (now + relativedelta(months=+1)).strftime("%d.%m.%Y")
    return '{0} - {1}'.format(gotDate, takeDate)

def getMonitorChats():
    """Получить список всех чатов, где сообщество занимается рассылкой

    Returns:
        list: список уникальных чатов сообщества
    """

    with open(MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)

        chat_list = []

        for conf in conf_list[1:]:
            for rcpn in conf["params"]["rcpns"]:
                chat_list.append(int(rcpn))

        return list(set(chat_list))
    
def getStoreMonitorChats():

    with open(STORE_MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)

        chat_list = []

        for conf in conf_list:
            for rcpn in conf["rcpns"]:
                chat_list.append(int(rcpn))

        return list(set(chat_list))
    
def getMonitorChatsTypes():
    """Получить список всех чатов и категорий, где сообщество занимается рассылкой

    Returns:
        dict: список чатовы
    """

    with open(MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)

        chat_dict = {}

        for conf in conf_list:
            for rcpn in conf["params"]["rcpns"]:

                if int(rcpn) in chat_dict: 

                    if conf['type'] in chat_dict[int(rcpn)]:
                        chat_dict[int(rcpn)][conf["type"]].append(conf["params"]["tag"])

                    else:
                        chat_dict[int(rcpn)].update({ conf["type"] : [conf["params"]["tag"]]})
                else:
                    chat_dict[int(rcpn)] = { conf["type"] : [conf["params"]["tag"]]}

        return chat_dict
    
def getActiveMonitorChatsTypes(conf_list):
    """Получить список всех активных чатов и категорий, где сообщество занимается рассылкой

    Args:
        conf_list (list): список конфигураций

    Returns:
        dict: список чатовы
    """

    chat_dict = {}

    for conf in conf_list:

        for rcpn in conf["params"]["rcpns"]:

            if int(rcpn) in chat_dict: 

                if conf['type'] in chat_dict[int(rcpn)]:
                    chat_dict[int(rcpn)][conf["type"]].append(conf["params"]["tag"])

                else:
                    chat_dict[int(rcpn)].update({ conf["type"] : [conf["params"]["tag"]]})
            else:
                chat_dict[int(rcpn)] = { conf["type"] : [conf["params"]["tag"]]}

    return chat_dict

    
def getFavInfo(text, item_index = 0, isPosredPresent = True):
    """Получить инфо для избранного из сообщения

    Args:
        text (string): текст сообщения
        item_index (int): порядковый номер лота в сообщении

    Returns:
        dict: словарь с инфо
    """
    fav_item = {}

    storeSelector = StoreSelector()
    storeSelector.url = CURRENT_POSRED

    if isPosredPresent:
        posred_domen = storeSelector.getStoreName()
        urls = [url for url in re.findall(RegexType.regex_store_url_bot, text) if url.find(posred_domen) == -1]
    else:
        urls = re.findall(RegexType.regex_store_url_bot, text)

    fav_item = storeSelector.selectStore(urls[item_index], not isPosredPresent)
    
    return fav_item

def flattenList(matrix):
    """сконвертировать матрицу в массив

    Args:
        list_of_lists (list of list): матрица

    Returns:
        list: одномерный массив
    """

    return list(chain.from_iterable(matrix))

def createItemPairs(items, message_img_limit = 10):
    """Сгруппировать товары в группы по message_img_limit шт

    Args:
        items (list of dict): список товаров

    Returns:
        list of list of dict: сгруппированный список товаров
    """

    items_parts = []
    
    
    i = 0
    for i in range(0, len(items) // message_img_limit):
        items_parts.append(items[(i) * message_img_limit : (i+1)* message_img_limit])

    if len(items) % message_img_limit != 0 and len(items_parts):
        items_parts.append(items[(i+1) * message_img_limit : len(items)])
    elif len(items) % message_img_limit != 0 and i == 0:
        items_parts.append(items[(i) * message_img_limit : len(items)])    

    return items_parts

def concatList(list1, list2):
    '''
    связывает два массива типа [ [...], ... [...]] поэлементно

    :param list1:
    :param list2:
    :return: список
    '''

    resultList = []
    for i in range(len(list1)):
        resultList.append([list1[i], list2[i]])

    return resultList

def flatTableParticipantList(particpantList):
    """Привести табличный вид списка участников в простой список позиций
       Исходный список формируется с помощью CollectOrdersSheet.getParticipantsList(namedRange)

    Args:
        particpantList (list of lists): табличный список участников
    """

    flatList = []
    for particpant in particpantList:
        info = {}
        try:
            info['id'] = re.search(RegexType.regex_vk_url, particpant[1]).group(0).split('id')[1].replace('";', '')
            info['items'] = particpant[0]
            flatList.append(info.copy())
        except:
            continue

    return flatList

def flatTopicParticipantList(particpantList):
    """Привести топиеовый вид списка участников в простой список позиций
       Исходный список формируется с помощью makeDistinctList + checkParticipants
       TO DO: унифицировать всё

    Args:
        particpantList (list of lists): табличный список участников
    """

    flatList = []
    for particpant in particpantList:
        pprint(particpant[0])
        info = {}
        try:
            info['id'] = particpant[1][0].split('id')[1]
            info['items'] = ", ".join(str(item) for item in particpant[0])
            flatList.append(info.copy())
        except Exception as e:
            pprint(e)
            continue

    return flatList
