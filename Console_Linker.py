from APIs.VkApi.VkInterface import VkApi as vk
from APIs.GoogleSheetsApi.CollectOrdersSheet import CollectOrdersSheet as collect_table
from APIs.GoogleSheetsApi.StoresCollectOrdersSheets import StoresCollectOrdersSheets
from traceback import format_exc, print_exc
from pprint import pprint 
from confings.Consts import OrdersConsts, RegexType, VkConsts, PosrednikConsts
from confings.Messages import Messages
import re
from time import sleep
from datetime import datetime
from SQLS import DB_Operations
from APIs.PosredApi.posredApi import PosredApi
from APIs.PosredApi.PosredOrderInfoClass import PosredOrderInfoClass
from APIs.utils import flattenList, flatTableParticipantList, flatTopicParticipantList, pickRightStoreSelector

def updateParticipantDB(participantList, collectId, isYstypka = False):
    """Обновить БД со списком участников и их позициями

    Args:
        participantList (list of lists): список участников
        collectId (string): id коллекта
        isYstypka (bool, optional): как часть уступки - нужно полностью переписывать весь коллект. Defaults to False.
    """
    isYstypkaFlag = isYstypka
    list = flatTableParticipantList(particpantList = participantList) if isYstypkaFlag else flatTopicParticipantList(particpantList = participantList)
    for item in list:
        DB_Operations.updateInsertParticipantsCollect(collect_id = collectId, user_id = item['id'], items = item['items'], isYstypka = isYstypkaFlag)    
        isYstypkaFlag = False

def createOrderList(collectList = [], indList = [], storeCollectList = []):
    """Сгенерить общий список заказов

    Args:
        collectList (list, optional): Список коллективок. Defaults to [].
        indList (list, optional): Список инд. Defaults to [].
        storeCollectList (list, optional): Список закупок. Defaults to [].

    Returns:
        list: общий список заказов с учётом их типа
    """

    orderList = [[OrdersConsts.CollectTypes.collect, f'C{collect}'] for collect in collectList if collect != '']
    orderList.extend([[OrdersConsts.CollectTypes.collect, f'I{ind}'] for ind in indList if ind != ''])
    orderList.extend([[OrdersConsts.CollectTypes.store, store] for store in storeCollectList if store != ''])

    return orderList


def createNamedRange(spId):
    """Генерирует именованный диапозон. Нужно доработать

    Args:
        spId (int): id листа таблицы

    Returns:
        string, string: именованный диапозон и айди коллекта для БД
    """
    namedRange = 'D'
    collect_id = ''
    collect_type = ''

    if spId == collect_table.sp.spreadsheetsIds['Дашины лоты'][0]:
        collect_type = "C"
        namedRange +='Collect'
    else:
        collect_type = 'I'
        namedRange += 'Ind'

    num = str(DB_Operations.getMaxCollectId(collect_type) + 1)
    namedRange += str(num)
    collect_id = collect_type + num

    return namedRange, collect_id

def strToList(string):
    '''
    Переводит строку в отсортированный список

    :param string:
    :return:
    '''

    list = string.split(", ")
    list = [int(x) for x in list]
    list.sort()

    return list

def checkItems(itemsList, itemsNumList):
    '''
    Проверка на повтор айтемов

    :param itemsList:
    :param itemsNumList:
    :return:
    '''

    correctItemsList = itemsList.copy()

    for i in itemsList:
        try:
            itemsNumList.remove(int(i))
        except:
            correctItemsList.remove(i)
            print("it was referenced before")

    return correctItemsList

def tryMakeCorrectItemList(inp, items_num, participant, correctList):
    '''
    Добавление участника и его айтемов в общий список

    :param inp:
    :param items_num:
    :param participant:
    :param correctList:
    :return:
    '''

    if len(inp) > 0 and inp != "-":
        listInp = checkItems(strToList(inp), items_num)
        correctList.append((listInp, participant))


def checkParticipants(participantsList, items_num):
    '''
    Проверка айтемов и участников

    :param participantsList:
    :param items_num:
    :return:
    '''
    items_num = [i + 1 for i in range(items_num)]

    print('\n====================================\n')
    print("let's check items and participants!")
    correctList = []

    flag = 0

    while len(items_num)!=0:

        if flag == 0:
            for i in range(len(participantsList)):
                inp = input("{0} : ".format(participantsList[i][1]))
                tryMakeCorrectItemList(inp, items_num, participantsList[i], correctList)
                if len(items_num) == 0: break
        elif flag == 1:
            if len(items_num) != 0:

                print('\n===== Remains')
                pprint(items_num)
                print("Amount of items: ", len(items_num) )
                inp = input("There are {} items, which were not used! Add participants? y/n: ".format(len(items_num)))
                if inp == "y":
                    inp = int(input("How many: "))

                    for i in range(inp):
                        id = input("Enter vk url. if it's you, enter 'Мне': ' ")

                        try:
                            name, id = vk.get_tuple_name(id)
                        except:
                            name = id
                            id = '0'

                        items = input("Items: ")
                        if id == "0":
                            tryMakeCorrectItemList(items, items_num, name, correctList)
                        else:
                            tryMakeCorrectItemList(items, items_num, (id, name), correctList)
        else:
            print('\n===== Free')
            pprint(items_num)
            print("Amount of items: ", len(items_num))
            for x in items_num:
                correctList.append(([x], " "))
            items_num = []
        flag += 1

    return correctList


def transformToTableFormat(participantsList):
    '''
    Переводит список позиций и участников в табличный вид для обновления таблицы

    :param participantsList: Список позиций и участников
    :return: возвращает словарь
    '''

    pList = []
    for p in participantsList:
        if isinstance(p[1], str):
            hyperlink = p[1]
        else:
            hyperlink = '=HYPERLINK("{0}"; "{1}")'.format(p[1][0],p[1][1])
        pList.append((p[0],hyperlink))

    pList = \
        { "participants" : len(pList),
          "participantList": pList,
        }

    return pList


def getIdFromUrl(url):
    '''
    Получает номер id пользователя vk из ссылки

    :param url: ссылка на пользователя в формате https://vk.com/id{числа}
    :return: возвращает часть строки, начиная с id
    '''

    return re.findall(r"id\d+", url)[0]

def transformToTopicFormat(participantsList):
    '''
    Переводит список позиций и участников в строковый вид для поста в обсуждении

    :param participantsList: Список позиций и участников
    :return: возвращает строчку
    '''

    pList = ""

    for p in participantsList:

        if isinstance(p[0], list):
            items = collect_table.sp.listToString(p[0])
        else:
            items = p[0]

        try:
            participant = "@{0}({1})".format(getIdFromUrl(p[1][0]), p[1][1])
        except:
            participant = p[1]
        pList += "{0} - {1}\n".format(items, participant)

    return pList

def tableToTopic(participantsList, paymentInfo):
    '''
    Из формата для таблиц переводит в формат для обсуждения

    :param participantsList: Список позиций и участников
    :return: возвращает строчку
    '''

    pList = ""

    for p in participantsList:

        p_url = re.findall('"(.+)";', p[1])

        try:
            p_name =  re.findall('; "(.+)"\)', p[1])[0]
            p[1] = [p_url[0], p_name]
        except:
            pass

    topicFormat = transformToTopicFormat(participantsList)

    topicFormat = topicFormat.split('\n')


    for i in range(len(topicFormat)):
        try:
            topicFormat[i] += ' ' + paymentInfo[i]
        except:
            pass


    topicFormat = "".join([str(item) + '\n' for item in topicFormat])

    return topicFormat

def makeDistinctList(post_url):
    '''
    Создаёт список уникальных пользователей с нескольких/одной записи

    :param post_url: список адресов записей на стене сообщества
    :return:
    '''

    participantsList = []
    for url in post_url:
        participantsList.append(vk.get_active_comments_users_list(url))

    pl = []
    for i in range(len(participantsList)):
            pl = list(set(pl + participantsList[i][0]))

    return pl

def getCollectId(collectType, collectNum):

    letter = "C" if collectType == "Коллективка" else "I"
    return f"{letter}{collectNum}"

def createTableTopic(post_url, site_url ='', spId=0, topic_id=0, items=0, img_url = ''):
    '''
    Создаёт таблицу и комент в обсуждении по заданным параметрам

    :param post_url: список адресов записей на стене сообщества
    :param spId:
    :param topic_id:
    :param items:
    :param img_url:
    :return:
    '''

    item = {}
    if site_url != '':
        store_selector = pickRightStoreSelector(url = site_url)
        item = store_selector.selectStore(url = site_url, isAdmin = True)
        if len(img_url) == 0:
            img_url = item.mainPhoto

    #-- пытаемся найти заказ у посредника
    posred_info = PosredOrderInfoClass()
    if item.country == OrdersConsts.OrderTypes.jp: # на текущий момент нужно только для Яп заказов
        posred_selector = PosredApi.pickRightPosredByOrderType(order_type = item.country)[PosrednikConsts.DaromJp]
        active_orders = posred_selector.get_active_orders()

        for active_order in active_orders.keys():
            if active_orders[active_order].product_id != item.id:
                continue
            else:
                posred_info = active_orders[active_order]
                posred_url = PosredApi.getPosredOrderByOrderId(order_id= posred_info.posred_id, 
                                                formatted_order_id = posred_selector.get_num_id(id = posred_info.posred_id))
                posred_info.set_posred_url(url = posred_url)
                break        
    #--

    namedRange, collect_id = createNamedRange(spId)

    participantsList = makeDistinctList(post_url) if post_url[0] != '' else []
    participantsList = checkParticipants(participantsList, items)
    participantsList.sort()

    mes = Messages.mes_collect_info(collectId = collect_id,
                                    participantList = transformToTopicFormat(participantsList), 
                                    lotWallUrl = post_url, siteName = item.siteName,
                                    where = item.country)

    topicInfo = vk.post_comment(topic_id = topic_id, message=mes, img_urls=[img_url])
 
    collect_table.createTable(spId, namedRange, participants = items, image = topicInfo[1][0], item = item, posredInfo = posred_info)

    collect_table.updateTable(namedRange, transformToTableFormat(participantsList), topicInfo[0])
    
    DB_Operations.updateCollectSelector(collectId = collect_id, sheet_or_range = namedRange,
                                        topic_id = topicInfo[2]['topic_id'], comment_id = topicInfo[2]['comment_id'],
                                        posred_id = posred_info.posred_id)
    updateParticipantDB(participantList = participantsList, collectId = namedRange.replace('D', '').replace('nd', '').replace('ollect', ''))
    
def ShipmentToRussiaEvent(orderList, toSpId = ''):
    """Активирует переброс лота с одного листа на другой

    Args:
        orderList (list): список заказов
        toSpId (int, optional): id листа. Defaults to collect_table.sp.spreadsheetsIds['Дашины лоты (Архив)'][0].
    """
    if orderList:
        toSpId = collect_table.sp.spreadsheetsIds['Дашины лоты (Архив)'][0]

        namedRangeList = [f'DCollect{order_number[1][1:]}' for order_number in orderList if order_number[1][0].find('C')>-1]
        namedRangeList.extend([f'DInd{order_number[1][1:]}' for order_number in orderList if order_number[1][0].find('I')>-1])

        for namedRange in namedRangeList:
            collect_table.moveTable(toSpId , namedRange)

def ArchiveCollects():
    """Отправить заказ в архив
    """

    print('\nВыберите:\n' + Messages.formConsoleListMes(info_list = ['коллекты/инды', 'закупки']))
    choise = int(input('Выбор: '))
    
    if choise == 1:
        lists = [ collect_table.sp.spreadsheetsIds['Дашины лоты (Архив)'][0],
                ]
        
        lists_name = ['Дашины лоты (Архив)']

        print('\nВыберите лист из таблицы:\n' + Messages.formConsoleListMes(info_list = lists_name))
        choise1 = int(input('Выбор: '))
        spId = lists[choise1 - 1]
        orderList = handle_ids_insert(isStores = False)
        ShipmentToRussiaEvent(toSpId = spId, orderList = orderList)

    elif choise == 2:
    
        order_title = input('\nВведите название закупки: ')
        is_exists = DB_Operations.isStoreCollectIxists(collect_title = order_title)

        if is_exists:
            sheet_id = DB_Operations.getStoresCollectSheetId(collect_id = order_title)
            storesCollectOrdersSheets.archiveStoreCollect(list_id = sheet_id)
        else:
            print('\nТакой закупки нет!\n')

def changeStatus(stat, orderList, payment = ''):
    # на руках
    
    if stat.lower().find('на руках') > -1:
        collectIndList = [order for order in orderList if order[0] == OrdersConsts.CollectTypes.collect]
        ShipmentToRussiaEvent(orderList = collectIndList)

        # если сразу ехало на получателя
        if stat.lower().find(' y ') > -1:
            participants = DB_Operations.getOrderParticipants(collect_id = item[1], collect_type = item[0])
            for participant in participants:
                DB_Operations.updateSentStatusForParticipant(collect_id = item[1],
                                                            collect_type = item[0],
                                                            user_id = participant)            

        storeList = [order for order in orderList if order[0] == OrdersConsts.CollectTypes.store]
        for item in storeList:
            list_id = DB_Operations.getStoresCollectSheetId(collect_id = item[1])
            storesCollectOrdersSheets.setStoresCollectRecieved(list_id = list_id)
    
    # топики в вк
    for item in orderList:
        sleep(5)
        pay = ''
        try:
            collectTopicInfo = DB_Operations.getCollectTopicComment(collect_id = item[1], collect_type = item[0])
            vk.edit_collects_activity_comment(topic_id = collectTopicInfo[0], comment_id = collectTopicInfo[1], 
                                              status_text = stat, participant_text = pay)
            DB_Operations.updateCollectSelector(collectType = item[0], collectId = item[1], status = stat)
        except Exception as e:
            pprint(e)
            print_exc()

def changePositions(userList):
    for ystypka in userList:
        collect_id = ''
        lot = ''
        collect_type = OrdersConsts.CollectTypes.collect

        if ystypka['collect'].isdigit():
            lot = "Collect{}".format(int(ystypka['collect']))
            collect_id = 'C{}'.format(int(ystypka['collect']))
        elif ystypka['collect'][1:].isdigit():
            lot = "Ind{}".format(ystypka['collect'][1:])
            collect_id = 'I{}'.format(ystypka['collect'][1:])
        else:
            lot = ystypka['collect']
            collect_id = ystypka['collect']
            collect_type = OrdersConsts.CollectTypes.store

        #TO DO: Поменять логику, нахера делать ревёрс
        if collect_type == OrdersConsts.CollectTypes.collect:

            user_info = list(vk.get_tuple_name(ystypka['url']))
            user_info.reverse()
            user_info = [[ystypka['collect_items'], user_info]]

            newParticipants = transformToTableFormat(user_info)
            try:
                actualParticipants, paymentInfo = collect_table.changePositions('D'+lot, newParticipants["participantList"], ystypka['payment_status'])
            except:
                actualParticipants, paymentInfo = collect_table.changePositions('L'+lot, newParticipants["participantList"], ystypka['payment_status'])

            updateParticipantDB(participantList = actualParticipants, collectId = collect_id, isYstypka = True)

            actualParticipants = tableToTopic(actualParticipants, paymentInfo)
        elif collect_type == OrdersConsts.CollectTypes.store:
            user_info = {}
            user_info['user_name'], user_info['user_url'] = vk.get_tuple_name(user_info['user_url'])
            user_info['items'] = ystypka['collect_items']
            user_info['id'] = user_info['user_url'].split('/')[-1]

            
            storesCollectOrdersSheets.addParticipants(list_id = DB_Operations.getStoresCollectSheetId(collect_id = collect_id), 
                                                      new_participant_list = [user_info], 
                                                      participant_count_old = DB_Operations.getParticipantsInStoreCollectCount(collect_id = collect_id))

            DB_Operations.updateInsertParticipantsCollect(collect_type = collect_type, collect_id = collect_id, 
                                                          user_id = user_info['id'], items = user_info['items'])    

        topicCollectInfo = DB_Operations.getCollectTopicComment(collect_id = collect_id)
        vk.edit_collects_activity_comment(topic_id = topicCollectInfo[0], comment_id = topicCollectInfo[1], 
                                          participant_text = actualParticipants)

def storeCollectActivities(topicList):

    order_title = input('\nВведите название закупки: ')
    is_exists = DB_Operations.isStoreCollectIxists(collect_title = order_title)

    if not is_exists:

        status = flattenList(DB_Operations.getCollectStatuses())
        status_text = status[0]

        orderTypesList = [orderType.value for orderType in OrdersConsts.OrderTypes]
        order_type = int(input(f'\nВыберите тип закупки:\n{Messages.formConsoleListMes(info_list = orderTypesList)}'))
        order_type =  OrdersConsts.OrderTypes(orderTypesList[order_type-1])

        topicOrdersList = [topic for topic in topicList 
                        if re.search(RegexType.regex_collect_orders_topics, topic['title'].lower())]
        
        topic_order = int(input(f'\nВыберите обсуждение:\n{Messages.formConsoleListMes(info_list = [topic["title"] for topic in topicOrdersList])}\n'))
        topic_order = topicOrdersList[topic_order - 1]['id']          
        
        order_title += f' #{DB_Operations.getMaxStoreCollectId(collect_title = order_title.split(" ")[0]) + 1}'

        wallPost = input('\nВведите ссылку на набор. (might be empty): ')

        items_info = {}
    else:
        collectTopicInfo = DB_Operations.getCollectTopicComment(collect_id = order_title, collect_type = OrdersConsts.CollectTypes.store)
        comment=vk.find_board_comment(topic_id = collectTopicInfo[0], comment_id = collectTopicInfo[1])
        comment_text = comment['text']
        item_urls = re.findall(RegexType.regex_url, comment_text)
        items_info = {url: {"item_name": '', "item_price": '', "users": []} for url in item_urls if url.find('vk') < 0}

    img = input('\nКартинки через запятую(, ) (might be empty): ')
    img = [] if img.split(', ') == [''] else img.split(', ')
    
    print('\nПодготовим участников.')
    print('\nTo stop enter any symbol\n')
    participant_list = []
    
    i = 0
    while True:
        user_info = {}
        i += 1
        user_info['user_url'] = input('user{0} URL: '.format(i))
        if user_info['user_url'].find('https://vk.com') < 0 and user_info['user_url'].lower().find('мне') < 0: 
            break
        if user_info['user_url'].lower().find('мне') >= 0:
            user_info['user_name'] = 'Мне'
            user_info['user_url'] = ''
        else:
            user_info['user_name'], user_info['user_url'] = vk.get_tuple_name(user_info['user_url'])
        
        user_info['items'] = input('позиции через запятую(, ): ')
        pprint(f'У пользователя {len(user_info["items"].split(", "))} позиций - разберём каждую')
        for item in user_info["items"].split(", "):
            item_url = input(f'{item} url: ')
            if item_url in items_info:
                items_info[item_url]['users'].append(vk.get_name(user_info['user_url'].split('/')[-1]) if user_info['user_url'] else 'Мне')
            else:
                item_name = input(f'{item} название: ')
                item_price = input(f'{item} цена: ')
                items_info[item_url] = {'users': [vk.get_name(user_info['user_url'].split('/')[-1]) if user_info['user_url'] else 'Мне'],
                                        'item_name': item_name,
                                        'item_price': item_price}

        participant_list.append(user_info.copy())
    
    if not is_exists:
        mes = Messages.formStoresCollect(collect_title = order_title, status = status_text,
                                        items_info = items_info, wall_post_url = wallPost)
        
        topicInfo = vk.post_comment(topic_id = topic_order, message = mes, img_urls=img)
        
        list_id = storesCollectOrdersSheets.createNewStoresCollect(title = order_title, topic_url = topicInfo[0],
                                                        participant_count = len(participant_list),
                                                        order_type = order_type)
        storesCollectOrdersSheets.updateStoresCollect(list_id = list_id, participant_list = participant_list,
                                                    participant_count_old = len(participant_list))
        
        DB_Operations.updateCollectSelector(collectType = OrdersConsts.CollectTypes.store, collectId = order_title, 
                                            sheet_or_range = list_id,
                                            topic_id = topicInfo[2]['topic_id'], comment_id = topicInfo[2]['comment_id'])
        
    else:
        collectTopicInfo = DB_Operations.getCollectTopicComment(collect_id = order_title, collect_type = OrdersConsts.CollectTypes.store)
        comment=vk.find_board_comment(topic_id = collectTopicInfo[0], comment_id = collectTopicInfo[1])
        old_text = comment['text']

        participants_start_part = re.search('\n\n\d', old_text).span()[1] - 1
        participants_end_part = re.search('\n\nПоедет', old_text).span()[0] + 1

        items_info = {info_key:items_info[info_key] for info_key in items_info.keys() if items_info[info_key]['users']}

        index_number = int(re.findall(r"\n\d+\. ", old_text)[-1].replace('\n', '').replace('. ', ''))
        participant_mes = old_text[participants_start_part:participants_end_part] + '\n' + Messages.formStoreCollectItemsList(items_info = items_info, index = index_number) + '\n'

        vk.edit_collects_activity_comment(topic_id = collectTopicInfo[0], comment_id = collectTopicInfo[1],
                                            participant_text = participant_mes, img_urls = img)
        
        # Проверяем есть ли в списке уже присутствующие 
        existing_participants = [participant for participant in participant_list if participant['user_url'] and 
                    DB_Operations.ifParticipantInStoreCollectExist(collect_id = order_title, 
                                                                   user_id = participant['user_url'].split('/')[-1].replace('id', ''))]        
        new_participant_list = [participant for participant in participant_list if participant['user_url'] and 
                    not DB_Operations.ifParticipantInStoreCollectExist(collect_id = order_title, 
                                                                   user_id = participant['user_url'].split('/')[-1].replace('id', ''))]        

        sheet_id = DB_Operations.getStoresCollectSheetId(collect_id = order_title)
        
        if new_participant_list:
            participant_count_old = DB_Operations.getParticipantsInStoreCollectCount(collect_id = order_title)
            storesCollectOrdersSheets.addParticipants(list_id = sheet_id, new_participant_list = participant_list,
                                                        participant_count_old = participant_count_old)
        if existing_participants:
            storesCollectOrdersSheets.updateParticipantItems(list_id = sheet_id, participant_list = existing_participants)

    for participant in participant_list:
        if participant['user_url']:
            DB_Operations.updateInsertParticipantsCollect(  collect_type = OrdersConsts.CollectTypes.store, collect_id = order_title, 
                                                            user_id = participant['user_url'].split('/')[-1].replace('id', ''), 
                                                            items = participant['items'])


def handle_ids_insert(isCollect = True, isInd = True, isStores = True):

    if isCollect:
        collectList = input("Enter collect's num using comma(, ) (might be empty): ")
        collectList = collectList.split(', ')
        collectList = [int(x) for x in collectList if x.isdigit()]
        collectList.sort()
    else:
        collectList = []

    if isInd:
        indList = input("Enter ind's num using comma(, ) (might be empty): ")
        indList = indList.split(', ')
        indList = [int(x) for x in indList if x.isdigit()]
        indList.sort()
    else:
        indList = []

    if isStores:
        storeCollectList = input("Enter storeCollect title using comma(, ) (might be empty): ")
        storeCollectList = storeCollectList.split(', ')
    else:
        storeCollectList = []

    return createOrderList(collectList = collectList, indList = indList, storeCollectList = storeCollectList)


def console():

    choise = 0
    topicList = vk.get_topics()
    albumList = vk.get_albums()

    while choise != 3:      
      try: 
        choiseList = ['Сделать лот', 'Отправки в РФ', 'Выход', 'Забанить', 
                      'Уступки', 'Обновление статуса заказов', 'Удаление фотографий', 
                      'Сформировать посылку', 'Обновление статуса посылки', 'Сделать/Добавить_в закупку',
                      'Изменить номер заказа посреда']
        choise = int(input('\nВведите номер:\n' + Messages.formConsoleListMes(info_list = choiseList, offset = 2) + '\nВыбор: '))

        if choise == 1:
            topicIdCollect = [topic['id'] for topic in topicList 
                              if topic['title'].lower().find('лоты') > -1][0]

            lists = [ collect_table.sp.spreadsheetsIds['Дашины лоты'][0],
                    collect_table.sp.spreadsheetsIds['Дашины индивидуалки'][0],
                    ]
            lists_name = ['Дашины лоты', 'Дашины индивидуалки']
            

            print('\nВыберите лист из таблицы:\n' + Messages.formConsoleListMes(info_list = lists_name))
            choise1 = int(input('Выбор: '))

            spId = lists[choise1-1]

            site_url = input('\nEnter the site url (might be empty): ')
           
            wallPosts = input('\nEnter the vk posts. If more than 1 - use space. (might be empty): ')
            wallPosts = wallPosts.split(' ')

            img = input('\nEnter the image url (might be empty): ')

            items = int(input('\nHow many items are there? '))

            createTableTopic(wallPosts, site_url, spId=spId,
                             topic_id = topicIdCollect, items=items, img_url=img)

        elif choise == 2:

            ArchiveCollects()

        elif choise == 4:

            user_list = []
            print('\nTo stop enter any symbol\n')

            i = 0

            while True:
                i += 1
                url = input('user{0} URL: '.format(i))
                if url.find('https://vk.com') < 0: break

                commentary = input('user{0} commentary: '.format(i))

                user_list.append({'id': vk.get_id(url.replace('https://vk.com/', '')), 'comment': commentary })

            for user in user_list:
                vk.ban_users(user)

        elif choise == 5:

            user_list = []
            print('\nTo stop enter any symbol\n')
            print('Если индивидуалка, то прицепить любой символ перед номером. Пример: и56')
            print('Если закупка, то название закупки и позиции. Пример: PLUSH SHOP #1  - плюш №1')
            print('Запись в формате: 213 - 1, 2, 4\n')

            i = 0

            while True:
                user_info = {}
                i += 1
                user_info['url'] = input('user{0} URL: '.format(i))
                if user_info['url'].find('https://vk.com') < 0: 
                    break
                
                user_info['collect'], user_info['collect_items'] = input('лот - уступка : '.format(i)).split(' - ')
                
                payed = input('Позиции оплачены? y/n: ')
                user_info['payment_status'] = 0 if payed.lower() != 'y' else 1
                
                user_list.append(user_info.copy())

            changePositions(user_list)
        elif choise == 6:
                        
            status = flattenList(DB_Operations.getCollectStatuses())

            while True:
                    print('\nTo stop enter any symbol\n')
                    print('\nВыберите статус:\n' + Messages.formConsoleListMes(info_list = status))

                    choise1 = int(input('Выбор: '))
                    stat = status[choise1-1]
                    payment = ''
                    orderList = handle_ids_insert()
                    changeStatus(stat, orderList, payment)

        elif choise == 7:

            print('\nВыберите альбом:\n' + Messages.formConsoleListMes(info_list = [x['title'] for x in albumList]))
            choiseAlbum = int(input('Выбор: '))
            album = albumList[choiseAlbum-1]

            date = input('Введите дату, до которой нужно удалить фотографии (ДД.ММ.ГГГГ): ')
            date = datetime.strptime(date, '%d.%m.%Y').date()

            vk.delete_photos(album_id = album['id'], end_date = date)

        elif choise == 8:
            posred_id = input('id посылки у посредника: ')
            status = flattenList(DB_Operations.getCollectStatuses())
            topicIdParcels = [topic['id'] for topic in topicList 
                              if topic['title'].lower().find('посылки') > -1][0]
            parcel_id = DB_Operations.getMaxCollectParcelId() + 1 

            print('\nВыберите статус:\n' + Messages.formConsoleListMes(info_list = status))
            choiseStatus = int(input('Выбор: '))
            stat = status[choiseStatus-1]


            img = input('\nEnter the image url using comma(, ) (might be empty): ')
            img = img.split(', ')

            posred = PosredApi.getPosredByParcelId(parcel_id = posred_id)
            orders = posred.get_parcel_orders(parcel_id = posred_id)

            present_collects = DB_Operations.getCollectsByPosredId(posred_ids = orders)

            present_posred_ids = [present_collect[2] for present_collect in present_collects]
            unpresent_orders = [order for order in orders if order not in present_posred_ids]

            print(f'Неиспользованные лоты: {unpresent_orders}')

            DB_Operations.updateInsertCollectParcel(parcel_id = parcel_id, status = stat)

            changeStatus(stat, present_collects)
            collectListUrl = []
            indListUrl = []

            for item in present_collects:
                #collectTopicInfo = DB_Operations.getCollectTopicComment(collect_id = item[1], collect_type = item[0])
                topic_url_template = f'[https://vk.com/topic-{vk.get_current_group_id()}_{item[3]}?post={item[4]}|'+'{}]'
                if item[0] == OrdersConsts.CollectTypes.store:
                    collectListUrl.append(topic_url_template.format(item[1]))
                elif item[0] == OrdersConsts.CollectTypes.collect:
                    if item[1][0] == 'I':
                        indListUrl.append(topic_url_template.format(item[1][1:]))
                    elif item[1][0] == 'C':
                        collectListUrl.append(topic_url_template.format(item[1][1:]))

            mes = Messages.formParcelCollectMes(parcel_id=parcel_id, status = stat, 
                                                collect_dict= {'collects': collectListUrl, 'inds': indListUrl })
            topicInfo = vk.post_comment(topic_id = topicIdParcels, message=mes, img_urls=img)

            DB_Operations.updateInsertCollectParcel(parcel_id = parcel_id, topic_id = topicInfo[2]['topic_id'], comment_id = topicInfo[2]['comment_id'])

            for item in present_collects:
                DB_Operations.updateCollectSelector(collectType = item[0], collectId = item[1], parcel_id = parcel_id, status = stat)

            
        elif choise == 9:

            status = flattenList(DB_Operations.getCollectStatuses())

            parcel_id = int(input('\nВведите номер посылки: '))

            print('\nВыберите статус:\n' + Messages.formConsoleListMes(info_list = status))
            choiseStatus = int(input('Выбор: '))
            stat = status[choiseStatus-1]

            DB_Operations.updateInsertCollectParcel(parcel_id = parcel_id, status = stat)
            parcelInfo = DB_Operations.getCollectParcel(parcel_id = parcel_id) # index: -2 -1
            vk.edit_collects_activity_comment(topic_id = parcelInfo[-2], comment_id = parcelInfo[-1],
                                       status_text= stat, typeChange = VkConsts.VkTopicCommentChangeType.parcel)

            collectList = DB_Operations.getAllCollectsInParcel(parcel_id = parcel_id)
            changeStatus(stat = stat, orderList = collectList)

        elif choise == 10:
            storeCollectActivities(topicList = topicList)
        elif choise == 11:
            ordersPrefix = {0: 'C', 1: 'I', 2: ''}
            choiseListPref = ['Коллект', 'Инда', 'Закупка']
            choise = int(input('\nВведите номер:\n' + Messages.formConsoleListMes(info_list = choiseListPref, offset = 2) + '\nВыбор: '))
            prefix = ordersPrefix[choise-1]
            collectId = prefix + input('Введите номер инды (для закупок название): ')
            posredId = input('Введите номер заказа у посреда: ')
            collectType = OrdersConsts.CollectTypes.store if choise == 3 else OrdersConsts.CollectTypes.collect
            DB_Operations.updateCollectSelector(collectId = collectId, collectType = collectType,
                                                posred_id = posredId)

      except Exception as e:
          print(f"\n===== ОШИБКА! \n{format_exc()} - {e}=====")
          continue

if __name__ == '__main__':


    collect_table = collect_table()
    storesCollectOrdersSheets = StoresCollectOrdersSheets()
    vk = vk()

    console()

