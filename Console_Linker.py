from VkApi.VkInterface import VkApi as vk
from APIs.GoogleSheetsApi.CollectOrdersSheet import CollectOrdersSheet as collect_table
from traceback import format_exc, print_exc
from pprint import pprint 
from confings.Consts import OrderTypes
from APIs.StoresApi.JpStoresApi.StoreSelector import StoreSelector
from confings.Messages import Messages
import re
from confings.Consts import VkTopicCommentChangeType
from time import sleep
from datetime import datetime
from SQLS import DB_Operations
from APIs.utils import flattenList, flatTableParticipantList, flatTopicParticipantList

def updateParticipantDB(participantList, collectId, isYstypka = False):
    """Обновить БД со списком участников и их позициями

    Args:
        participantList (list of lists): список участников
        collectId (string): id коллекта
        isYstypka (bool, optional): как часть уступки - нужно полностью переписывать весь коллект. Defaults to False.
    """

    list = flatTableParticipantList(particpantList = participantList) if isYstypka else flatTopicParticipantList(particpantList = participantList)
    for item in list:
        DB_Operations.updateInsertParticipantsCollect(collect_id = collectId, user_id = item['id'], items = item['items'], isYstypka = isYstypka)    

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
    siteName = ''
    if site_url != '':
        item = store_selector.selectStore(site_url)
        if len(img_url) == 0:
            img_url = item['mainPhoto']

    namedRange, collect_id = createNamedRange(spId)

    participantsList = makeDistinctList(post_url) if post_url[0] != '' else []
    participantsList = checkParticipants(participantsList, items)
    participantsList.sort()

    mes = Messages.mes_collect_info(collectId = collect_id,
                                    participantList = transformToTopicFormat(participantsList), 
                                    lotWallUrl = post_url, siteName = item["siteName"])

    topicInfo = vk.post_comment(topic_id = topic_id, message=mes, img_urls=[img_url])

    collect_table.createTable(spId, namedRange, participants = items, image = topicInfo[1][0], item = item)

    collect_table.updateTable(namedRange, transformToTableFormat(participantsList), topicInfo[0])

    DB_Operations.updateCollect(collectId = collect_id, namedRange = namedRange,
                                topic_id = topicInfo[2]['topic_id'], comment_id = topicInfo[2]['comment_id'])
    updateParticipantDB(participantList = participantsList, collectId = namedRange.replace('D', '').replace('nd', '').replace('ollect', ''))


def ShipmentToRussiaEvent(toSpId, collectList, indList):
    '''
    Активирует переброс лота с одного листа на другой
    :param toSpId:
    :param collectList: список номеров коллективок
    :param indList: список номеров индивидуалок
    :return:
    '''

    lotList = {'DCollect': [x for x in collectList], 'DInd': [x for x in indList]}

    for key in lotList.keys():
        for i in range(len(lotList[key])):
            if lotList[key][i] != '':
                collect_table.moveTable(toSpId, key + lotList[key][i])

def changeStatus(stat, collectList, indList, payment):

    collect_list = [f'C{x}' if len(x)>0 else x for x in collectList if x != '']
    collect_list.extend([f'I{x}' if len(x)>0 else x for x in indList if x != ''])

    for collect_id in collect_list:

        pay = ''
        if payment == 'y':
            namedRange = collect_id.replace('C', 'DCollect') if collect_id.find('C') > -1 else collect_id.replace('I', 'DInd')
            pay = collect_table.getPaymentStatus(namedRange)
            participants = collect_table.getParticipantsList(namedRange)
            pay = tableToTopic(participants, pay)
        try:
            collectTopicInfo = DB_Operations.getCollectTopicComment(collect_id = collect_id)
            vk.edit_collects_activity_comment(topic_id = collectTopicInfo[0], comment_id = collectTopicInfo[1], 
                                              status_text = stat, participant_text = pay)
            DB_Operations.updateCollect(collectId = collect_id, status = stat)
        except Exception as e:
            pprint(e)
            print_exc()

def changePositions(userList):
    for ystypka in userList:
        collect_id = ''
        lot = ''

        if ystypka['collect'].isdigit():
            lot = "Collect{}".format(int(ystypka['collect']))
            collect_id = 'C{}'.format(int(ystypka['collect']))
        else:
            lot = "Ind{}".format(ystypka['collect'])
            collect_id = 'I{}'.format(ystypka['collect'])

        #TO DO: Поменять логику, нахера делать ревёрс
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

        topicCollectInfo = DB_Operations.getCollectTopicComment(collect_id = collect_id)
        vk.edit_collects_activity_comment(topic_id = topicCollectInfo[0], comment_id = topicCollectInfo[1], 
                                          participant_text = actualParticipants)


def console():

    choise = 0
    topicList = vk.get_topics()
    albumList = vk.get_albums()

    while choise != 3:      
      try: 
        choiseList = ['Сделать лот', 'Отправки в РФ', 'Выход', 'Забанить', 
                      'Уступки', 'Обновление статуса лотов', 'Удаление фотографий', 
                      'Сформировать посылку', 'Обновление статуса посылки', 'Сделать закупку']
        choise = int(input('\nВведите номер:\n' + Messages.formConsoleListMes(info_list = choiseList, offset = 2) + '\nВыбор: '))

        if choise == 1:

            topicIdCollect = [topic['id'] for topic in topicList 
                              if topic['title'].lower().find('лоты') > -1][0]

            lists = [ collect_table.sp.spreadsheetsIds['Дашины лоты'][0],
                    collect_table.sp.spreadsheetsIds['Дашины индивидуалки'][0],
                    collect_table.sp.spreadsheetsIds['ТестЛист'][0]
                    ]
            lists_name = ['Дашины лоты', 'Дашины индивидуалки', 'ТестЛист']
            

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

            lists = [ collect_table.sp.spreadsheetsIds['Дашины лоты (Архив)'][0],
                    collect_table.sp.spreadsheetsIds['ТестЛист'][0]
                    ]
            
            lists_name = ['Дашины лоты (Архив)', 'ТестЛист']

            print('\nВыберите лист из таблицы:\n' + Messages.formConsoleListMes(info_list = lists_name))
            choise1 = int(input('Выбор: '))

            spId = lists[choise1 - 1]

            collectList = input("Enter collect's num using comma(, ) (might be empty): ")
            collectList = collectList.split(', ')

            indList = input("Enter ind's num using comma(, ) (might be empty): ")
            indList = indList.split(', ')

            ShipmentToRussiaEvent(spId, collectList, indList)

        elif choise == 4:

            user_list = []
            print('\nTo stop enter any symbol\n')

            i = 0

            while True:
                i += 1
                url = input('user{0} URL: '.format(i))
                if url.find('https://vk.com') < 0: break

                commentary = input('user{0} commentary: '.format(i))

                user_list.append({'id': url, 'comment': commentary })

            vk.ban_users(user_list)

        elif choise == 5:

            user_list = []
            print('\nTo stop enter any symbol\n')
            print('Если индивидуалка, то прицепить любой символ перед номером. Пример: и56')
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

                    collectList = input("Enter collect's num using comma(, ) (might be empty): ")
                    collectList = collectList.split(', ')

                    indList = input("Enter ind's num using comma(, ) (might be empty): ")
                    indList = indList.split(', ')

                    payment = input('Нужна ли информация об оплатах? y/n: ')

                    changeStatus(stat, collectList, indList, payment)

        elif choise == 7:

            print('\nВыберите альбом:\n' + Messages.formConsoleListMes(info_list = [x['title'] for x in albumList]))
            choiseAlbum = int(input('Выбор: '))
            album = albumList[choiseAlbum-1]

            date = input('Введите дату, до которой нужно удалить фотографии (ДД.ММ.ГГГГ): ')
            date = datetime.strptime(date, '%d.%m.%Y').date()

            vk.delete_photos(album_id = album['id'], end_date = date)

        elif choise == 8:

            status = flattenList(DB_Operations.getCollectStatuses())
            topicIdParcels = [topic['id'] for topic in topicList 
                              if topic['title'].lower().find('посылки') > -1][0]
            parcel_id = DB_Operations.getMaxCollectParcelId() + 1 

            print('\nВыберите статус:\n' + Messages.formConsoleListMes(info_list = status))
            choiseStatus = int(input('Выбор: '))
            stat = status[choiseStatus-1]

            collectList = input("\nEnter collect's num using comma(, ) (might be empty): ")
            collectList = collectList.split(', ')

            indList = input("Enter ind's num using comma(, ) (might be empty): ")
            indList = indList.split(', ')

            img = input('\nEnter the image url using comma(, ) (might be empty): ')
            img = img.split(', ')

            mes = Messages.formParcelCollectMes(parcel_id=parcel_id, status = stat, 
                                                collect_dict= {'collects': collectList, 'inds': indList})

            topicInfo = vk.post_comment(topic_id = topicIdParcels, message=mes, img_urls=img)

            DB_Operations.updateInsertCollectParcel(parcel_id = parcel_id, status = stat,
                                                    topic_id = topicInfo[2]['topic_id'], comment_id = topicInfo[2]['comment_id'])
            
            collectList = [f'C{collect}' for collect in collectList if collect != '']
            indList = [f'I{ind}' for ind in indList if ind != '']
            collectList.extend(indList)

            for itemId in collectList:
                sleep(4)
                DB_Operations.updateCollect(collectId = itemId, status = stat, parcel_id = parcel_id)
                collectTopicInfo = DB_Operations.getCollectTopicComment(collect_id = itemId)
                vk.edit_collects_activity_comment(topic_id = collectTopicInfo[0], comment_id = collectTopicInfo[1],
                                           status_text = stat)
        elif choise == 9:

            status = flattenList(DB_Operations.getCollectStatuses())

            parcel_id = int(input('\nВведите номер посылки: '))

            print('\nВыберите статус:\n' + Messages.formConsoleListMes(info_list = status))
            choiseStatus = int(input('Выбор: '))
            stat = status[choiseStatus-1]

            DB_Operations.updateInsertCollectParcel(parcel_id = parcel_id, status = stat)
            parcelInfo = DB_Operations.getCollectParcel(parcel_id = parcel_id) # index: -2 -1
            vk.edit_collects_activity_comment(topic_id = parcelInfo[-2], comment_id = parcelInfo[-1],
                                       status_text= stat, typeChange = VkTopicCommentChangeType.parcel)

            collectList = DB_Operations.getAllCollectsInParcel(parcel_id = parcel_id)
            collectList = [collect[0] for collect in collectList]
            
            for itemId in collectList:
                pprint(itemId)
                sleep(4)
                DB_Operations.updateCollect(collectId = itemId, status = stat, parcel_id = parcel_id)
                collectTopicInfo = DB_Operations.getCollectTopicComment(collect_id = itemId)
                vk.edit_collects_activity_comment(topic_id = collectTopicInfo[0], comment_id = collectTopicInfo[1],
                                           status_text = stat)
        elif choise == 10:

            orderTypesList = [orderType.value for orderType in OrderTypes]
            order_type = int(input(f'\nВыберите тип закупки:\n{Messages.formConsoleListMes(info_list = orderTypesList)}'))
            order_type =  OrderTypes(orderTypesList[order_type-1])

            order_title = input('\nВведите название закупки: ')
            
            


      except Exception as e:
          print(f"\n===== ОШИБКА! \n{format_exc()} - {e}=====")
          continue

if __name__ == '__main__':


    collect_table = collect_table()
    vk = vk()
    store_selector = StoreSelector()

    console()

