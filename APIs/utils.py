
import os
import json
from confings.Consts import PathsConsts, RegexType, PosrednikConsts, OrdersConsts, VkConsts
import re
from itertools import chain
from pprint import pprint
from APIs.StoresApi.JpStoresApi.StoreSelector import StoreSelector as StoreSelectorJp
from APIs.StoresApi.USStoresApi.StoreSelector import StoreSelector as StoreSelectorUs
from random import randint
import requests
from traceback import print_exc

def generate_random_integer():
    return randint(0,2147483647)

def formShortList(storeList):

    store_selector = StoreSelectorJp()
    storeListShort = []
    for store in storeList:
        store_selector.url = store
        storeListShort.append(store_selector.getStoreName())
    return storeListShort

def pickRightStoreSelector(url, payloadCountry = None):

    store_selector = StoreSelectorJp()
    store_selector_us = StoreSelectorUs()

    store_selector.url = url
    current_store_name = store_selector.getStoreName()

    if payloadCountry == VkConsts.PayloadPriceCheckCountry.us:
        return store_selector_us
    elif payloadCountry == VkConsts.PayloadPriceCheckCountry.jpy: 
        return store_selector
    else:
        if current_store_name in OrdersConsts.Stores.JpStores:
            return store_selector
        else:
            return store_selector_us

def getChar(char, step):
    """Получить след символ

    Args:
        char (char): символ
        step (int): отступ от текущего символа

    Returns:
        char: след символ   
    """
    return chr(ord(char) + step)

def getMonitorChats():
    """Получить список всех чатов, где сообщество занимается рассылкой

    Returns:
        list: список уникальных чатов сообщества
    """

    with open(PathsConsts.MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)

        chat_list = []

        for conf in conf_list[1:]:
            for rcpn in conf["params"]["rcpns"]:
                chat_list.append(int(rcpn))

        return list(set(chat_list))
    
def getStoreMonitorChats():

    with open(PathsConsts.STORE_MONITOR_CONF_PATH, "r") as f: 
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

    with open(PathsConsts.MONITOR_CONF_PATH, "r") as f: 
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
    fav_item = None

    storeSelector = StoreSelectorJp()
    storeSelector.url = PosrednikConsts.CURRENT_POSRED

    if isPosredPresent:
        posred_domen = storeSelector.getStoreName()
        urls = [url for url in re.findall(RegexType.regex_store_url_bot, text) if url.find(posred_domen) == -1]
    else:
        urls = re.findall(RegexType.regex_store_url_bot, text)

    storeSelector = pickRightStoreSelector(url = urls[item_index])
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

def get_image_extension(url):
    """Получить формат файла изображения

    Args:
        url (string): путь до файла

    Returns:
        string: формат файла
    """
    extensions = ['.png', '.jpg', '.jpeg', '.gif']
    for ext in extensions:
        if ext in url:
            return ext
    return '.jpg'

def local_image_upload(url: str, tag:str, isFullPathNeeded = False) -> str:
    """Функция скачивает изображение по url и возвращает строчку с полученным именем файла

    Args:
        url (str): Ссылка на изображение

    Returns:
        str: Имя файла или пустая строка
    """
    try:
        extention = get_image_extension(url)
        filename = ''
        if extention != '':
            filename = f'new_image{randint(0,15000)}_{tag}' + extention
            response = requests.get(url)
            image = open(PathsConsts.TEMP_PHOTO_PATH + filename, 'wb')
            image.write(response.content)
            image.close()
        return PathsConsts.TEMP_PHOTO_PATH + filename if isFullPathNeeded else filename
    except:
        print_exc()
        local_image_upload(url, tag)

def createCollage(imagePaths, imagesPerRow = 3, spacing = 20):
    """
    Создает коллаж из изображений.
    
    :param image_paths: Список путей к изображениям
    :param imagesPerRow : Количество изображений в строке (по умолчанию 4)
    :param spacing: Расстояние между изображениями (по умолчанию 10 пикселей)
    """
    from PIL import Image
    if not imagePaths:
        return
    outputPath = PathsConsts.TEMP_PHOTO_PATH + f'new_collage_image{randint(0,15000)}.jpg'

    images = [Image.open(img_path) for img_path in imagePaths]
    widths, heights = zip(*(img.size for img in images))
    
    # Определяем размеры коллажа
    max_height_per_row = []
    current_row_width = 0
    current_row_heights = []
    rows_info = []
    
    for i, (w, h) in enumerate(zip(widths, heights)):
        current_row_width += w
        current_row_heights.append(h)
        
        # Если собрали imagesPerRow  изображений или это последнее изображение
        if (i + 1) % imagesPerRow  == 0 or i == len(images) - 1:
            max_height = max(current_row_heights)
            rows_info.append({
                "width": current_row_width,
                "height": max_height,
                "count": len(current_row_heights)
            })
            max_height_per_row.append(max_height)
            current_row_width = 0
            current_row_heights = []
    
    # Общая ширина коллажа — ширина самой широкой строки
    collage_width = max(row["width"] for row in rows_info)
    # Общая высота коллажа — сумма высот всех строк + отступы
    collage_height = sum(max_height_per_row) + (spacing * (len(rows_info) - 1))
    
    # Создаем новое изображение для коллажа
    collage = Image.new('RGB', (collage_width, collage_height), (255, 255, 255))
    
    # Вставляем изображения в коллаж
    x_offset, y_offset = 0, 0
    current_row = 0
    current_row_images = 0
    
    for i, img in enumerate(images):
        # Если строка заполнена, переходим на новую
        if i > 0 and i % imagesPerRow  == 0:
            y_offset += max_height_per_row[current_row] + spacing
            x_offset = 0
            current_row += 1
            current_row_images = 0
        
        # Вычисляем отступ по Y для выравнивания по высоте строки
        row_max_height = max_height_per_row[current_row]
        y_pos = y_offset + (row_max_height - img.size[1]) // 2  # Центрируем по вертикали
        
        collage.paste(img, (x_offset, y_pos))
        x_offset += img.size[0] + spacing
        current_row_images += 1
    
    collage.save(outputPath)
    for img in imagePaths:
        os.remove(img)

    return outputPath

def isExistingFile(path):
    """Проверяет, существует ли файл по указанному пути.

    Args:
        path (string): предполагаемый путь до файла

    Returns:
        bool: существование файла
    """

    return os.path.exists(path) and os.path.isfile(path)


