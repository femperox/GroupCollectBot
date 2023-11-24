from datetime import datetime
import os
import json
from confings.Consts import MONITOR_CONF_PATH, RegexType, STORE_MONITOR_CONF_PATH
import re

def getCurrentDate():
    """Получить текущую дату

    Returns:
        string: текущая дата
    """
    
    return datetime.now().strftime('%Y-%m-%d')

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
                    chat_dict[int(rcpn)][conf["type"]].append(conf["params"]["tag"])
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
                chat_dict[int(rcpn)][conf["type"]].append(conf["params"]["tag"])
            else:
                chat_dict[int(rcpn)] = { conf["type"] : [conf["params"]["tag"]]}

    return chat_dict

    
def getFavInfo(text, item_index = 0):
    """Получить инфо для избранного из сообщения

    Args:
        text (string): текст сообщения
        item_index (int): порядковый номер лота в сообщении

    Returns:
        dict: словарь с инфо
    """
    fav_item = {}

    fav_item['id'] = dict.fromkeys(re.findall(RegexType.regex_id , text))
    fav_item['id'].pop('auction/yauction', None)
    fav_item['id'] = list(fav_item['id'])[item_index].replace('auction/', '')
    
    fav_item['date_end'] = re.findall(RegexType.regex_date, text)[item_index].replace('Конец: ', '')

    return fav_item

