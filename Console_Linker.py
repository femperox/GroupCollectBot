from VkApi.VkInterface import VkApi as vk
from GoogleSheets.CollectOrdersSheet import CollectOrdersSheet as collect_table
from traceback import format_exc, print_exc
from pprint import pprint 
from JpStoresApi.StoreSelector import StoreSelector
from confings.Messages import Messages
import re
from datetime import datetime
from SQLS import DB_Operations
from APIs.utils import flattenList

def createNamedRange(spId, who, find):
    '''
    Генерирует именованный диапозон. Нужно доработать

    :param who:
    :param num:
    :param what:
    :return:
    '''

    # тут сделать проверку по айди
    result = who

    if spId == collect_table.sp.spreadsheetsIds['Дашины лоты'][0] or spId == collect_table.sp.spreadsheetsIds['Лерины лоты'][0]:
    # пока хз чё
        result += "Collect"
        find['key_word'] = 'Коллективка'
    else:
        result += 'Ind'
        find['key_word'] = 'Индивидуалка'

    num = int(vk.get_last_lot(find)) + 1
    result += str(num)

    return result

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


def createTableTopic(post_url, site_url ='', spId=0, topicName=0, items=0, img_url = ''):
    '''
    Создаёт таблицу и комент в обсуждении по заданным параметрам

    :param post_url: список адресов записей на стене сообщества
    :param spId:
    :param topicName:
    :param items:
    :param img_url:
    :return:
    '''

    if spId == collect_table.sp.spreadsheetsIds['Лерины лоты'][0]:
        letter = 'L'
        where = 'Железнодорожный'
    else:
        letter = 'D'
        where = 'Краснодар'

    find = {'topic_name': topicName, 'collect_type': 'Индивидуалка'}

    item = {}
    siteName = ''
    if site_url != '':
        item = store_selector.selectStore(site_url)
        siteName = f'( {item["siteName"]} )'
        if len(img_url) == 0:
            img_url = item['mainPhoto']

    namedRange = createNamedRange(spId, letter, find)

    participantsList = makeDistinctList(post_url) if post_url[0] != '' else []
    participantsList = checkParticipants(participantsList, items)
    participantsList.sort()

    collectType, collectNum = collect_table.sp.defineCollectType(namedRange)
    mes = Messages.mes_collect_info(collectType = collectType, collectNum = collectNum,
                                    participantList = transformToTopicFormat(participantsList), 
                                    lotWallUrl = post_url, siteName = siteName, 
                                    where = where)

    topicInfo = vk.post_comment(topic_name = topicName, message=mes, img_urls=[img_url])

    collect_table.createTable(spId, namedRange, participants = items, image = topicInfo[1][0], item = item)

    collect_table.updateTable(namedRange, transformToTableFormat(participantsList), topicInfo[0])

    return namedRange


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

def changeStatus(stat, collectList, indList, payment, topic_name = "❏ Лоты и индивидуалки"):


    lotList = {'DCollect': [int(x) if len(x)>0 else x for x in collectList], 'DInd': [int(x) if len(x)>0 else x for x in indList]}
    typeList = {'DCollect': 'Коллективка', 'DInd': 'Индивидуалка'}

    what_to_find = {"topic_name": topic_name} # "type": "Коллективка", "number": 234}

    for key in lotList.keys():
        what_to_find['type'] = typeList[key]
        for i in range(len(lotList[key])):
            if lotList[key][i] != '':
                what_to_find['number'] = lotList[key][i]
                pay = ''
                if payment == 'y':
                    pay = collect_table.getPaymentStatus('{0}{1}'.format(key, lotList[key][i]))
                    participants = collect_table.getParticipantsList('{0}{1}'.format(key, lotList[key][i]))
                    pay = tableToTopic(participants, pay)
                try:
                    vk.edit_status_comment(what_to_find, status= stat, payment= pay)
                    DB_Operations.updateCollect(what_to_find['type'], what_to_find['number'], stat)
                except Exception as e:
                    pprint(e)
                    print_exc()

def changePositions(userList, topic_name = "❏ Лоты и индивидуалки"):

    for yst in userList:

        try:
            number = int(yst[0])
            lot = "Collect{0}".format(number)
            type = "Коллективка"
        except:
            number = int(yst[0][1:])
            lot = "Ind{0}".format(number)
            type = "Индивидуалка"

        id = vk.get_tuple_name(yst[1][1])
        yst[1][1] = [id[1], id[0]]

        newParticipants = transformToTableFormat([yst[1]])
        try:
            actualParticipants, paymentInfo = collect_table.changePositions('D'+lot, newParticipants["participantList"], yst[2])
        except:
            actualParticipants, paymentInfo = collect_table.changePositions('L'+lot, newParticipants["participantList"], yst[2])


        actualParticipants = tableToTopic(actualParticipants, paymentInfo)


        what_to_find = {
            "topic_name": topic_name,
            "type": type,
            "number": number
        }

        vk.edit_comment(actualParticipants, what_to_find)


def console():

    choise = 0

    while choise != 3:

      
      try: 
        choiseList = ['Сделать лот', 'Отправки в РФ', 'Выход', 'Замена ссылок на теги',
                        'Забанить', 'Уступки', 'Обновление статуса лотов', 'Удаление фотографий']
        choise = int(input('\nВведите номер:\n' + Messages.formConsoleListMes(info_list = choiseList, offset = 2) + '\nВыбор: '))

        if choise == 1:

            topicName = "❏ Лоты и индивидуалки"

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


            namedRange = createTableTopic(wallPosts, site_url, spId=spId,
                                        topicName=topicName, items=items, img_url=img)

            collectType, collectNum = collect_table.sp.defineCollectType(namedRange)
            DB_Operations.insertCollect(collectType, collectNum, namedRange)

        elif choise == 2:

            lists = [ collect_table.sp.spreadsheetsIds['Дашины лоты (Архив)'][0],
                    collect_table.sp.spreadsheetsIds['Дашины лоты (Едет в РФ)'][0],
                    collect_table.sp.spreadsheetsIds['ТестЛист'][0]
                    ]
            
            lists_name = ['Дашины лоты (Архив)', 'Дашины лоты (Едет в РФ)', 'ТестЛист']

            print('\nВыберите лист из таблицы:\n' + Messages.formConsoleListMes(info_list = lists_name))
            choise1 = int(input('Выбор: '))

            spId = lists[choise1 - 1]

            collectList = input("Enter collect's num using comma(, ) (might be empty): ")
            collectList = collectList.split(', ')

            indList = input("Enter ind's num using comma(, ) (might be empty): ")
            indList = indList.split(', ')

            ShipmentToRussiaEvent(spId, collectList, indList)

        elif choise == 4:
            topics = [ '❏ Лоты и индивидуалки',
                        '❏ Заказы гашапонов',
                        '❏ Заказы с AmiAmi',
                        '❏ Коллект посылка до админа из Краснодара',
                        '❏ Коллект посылка до админа из Москвы'
            ]

            print('\nВыберите обсуждение:\n' + Messages.formConsoleListMes(info_list = topics, offset = 2))

            choise1 = int(input('Выбор: '))
            vk.replace_url(topics[choise1-1])

        elif choise == 5:

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

        elif choise == 6:

            user_list = []
            print('\nTo stop enter any symbol\n')
            print('Если индивидуалка, то прицепить любой символ перед номером. Пример: и56')
            print('Запись в формате: 213 - 1, 2, 4\n')

            i = 0

            while True:
                i += 1
                url = input('user{0} URL: '.format(i))
                if url.find('https://vk.com') < 0: break

                lot, items = input('лот - уступка : '.format(i)).split(' - ')
                #items = items.split(', ')
                payed = input('Позиции оплачены? y/n: ')
                payed = 0 if payed.lower() != 'y' else 1

                user_list.append([lot, [items, url], payed])

            changePositions(user_list)
        elif choise == 7:
                        
            status = flattenList(DB_Operations.getCollectStatuses())

            while True:
                    print('\nTo stop enter any symbol\n')
                    print('\nВыберите статус:\n' + Messages.formConsoleListMes(info_list = status))

                    choise1 = int(input('Выбор: '))
                    stat = status[choise1-1]
                    if stat == 'Едет в РФ':
                        print('Через запятую перечислите трек-номера\n')
                        trakcs = input('Треки: ').split(', ')

                        for trakc in trakcs:
                            stat += '\n' + trakc
                    if stat == 'Без статуса':
                        stat = ''

                    collectList = input("Enter collect's num using comma(, ) (might be empty): ")
                    collectList = collectList.split(', ')

                    indList = input("Enter ind's num using comma(, ) (might be empty): ")
                    indList = indList.split(', ')

                    payment = input('Нужна ли информация об оплатах? y/n: ')

                    changeStatus(stat, collectList, indList, payment)

        elif choise == 8:

                d = input('Введите дату, до которой нужно удалить фотографии: ')
                d = datetime.strptime(d, '%d.%m.%Y').date()

                album = 'Ваши хотелки'
                vk.delete_photos(album_name=album, end_date=d)

      except Exception as e:
          print(f"\n===== ОШИБКА! \n{format_exc()}=====")
          continue

if __name__ == '__main__':


    collect_table = collect_table()
    vk = vk()
    store_selector = StoreSelector()

    console()

