from GoogleSheets.ParentSheetClass import ParentSheetClass
from GoogleSheets.Spreadsheets.CollectOrdersSpreadsheet import CollectOrdersSpreadsheetClass
import re
import GoogleSheets.API.Cells_Editor as ce
from GoogleSheets.API.Styles.Borders import Borders as b
from GoogleSheets.API.Styles.Colors import Colors as c
from APIs.utils import concatList

class CollectOrdersSheet(ParentSheetClass):

    def __init__(self):

        super().__init__()
        self.setSpreadsheetId("collectOrdersList")
        self.sp = CollectOrdersSpreadsheetClass(self.getSheetListProperties())
        self.lastFree = 1

    def getPaymentStatus(self, namedRange):
        '''
        Информация о статусе оплат каждого участника

        :param namedRange: имя Именованного диапозона
        :return: список строк, состоящих из '+'
        '''

        info = self.getRowData(namedRange, cell_point=1)
        paymentInfo = []

        for row in info:

            payment = ''
            for column in row['values']:
                if column['effectiveFormat']['backgroundColor'] == c.light_green:
                    payment += '+'
            paymentInfo.append(payment)

        return paymentInfo

    def getOldUrls(self, namedRange):
        '''
        Информация о старом типе ссылок в таблице лота

        :param namedRange:
        :return:
        '''

        info = self.getRowData(namedRange, typeCalling=1)

        oldUrls = []

        for row in info:
            for column in row['values']:
                try:
                    oldUrls.append([column['formattedValue'], column['hyperlink']])
                except:
                    oldUrls.append([])

        return oldUrls

    def getPaymentAmount(self, namedRange):
        '''
        Информация о значениях оплат

        :param namedRange: имя Именованного диапозона
        :return: список сумм к оплате за каждую категорию
        '''

        info = self.getRowData(namedRange)
        paymentInfo = []

        for row in info:

            payment = []
            colors = []
            for column in row['values']:
                #формула
                colors.append(column['effectiveFormat']['backgroundColor'])
                try:
                    payment.append(column['userEnteredValue']['formulaValue'])
                except:
                    #значение
                    try:
                        payment.append(column['userEnteredValue']['numberValue'])
                    #пусто
                    except:
                        payment.append('')


            paymentInfo.append([payment,colors])

        return paymentInfo
    
    def getImageURLFromNamedRange(self, namedRange):
        '''
        Находит URL изображения, использованного в лоте, по информации об именованном диапозоне

        :param namedRange: имя Именованного диапозона
        :return: возвращает URL изображения
        '''

        imgUrl = self.getJsonNamedRange(namedRange, typeCalling = 1)
        imgUrl = imgUrl['values'][1][0]
        imgUrl = re.findall(r'"(\S+)"', imgUrl)
        imgUrl = imgUrl[0]

        return imgUrl

    def getParticipantsList(self, namedRange):
       '''
       Информация об участниках и их позициях

       :param namedRange:
       :return:
       '''

       info_urls = self.getJsonNamedRange(namedRange, typeCalling = 1)
       info_items = self.getJsonNamedRange(namedRange, typeCalling = 1, valueRenderOption= "FORMATTED_VALUE")


       info_urls = info_urls['values'][14:]
       info_items = info_items['values'][14:]

       i = 0
       participantList = []
       while info_urls[i][0] != "СУММАРНО":

           # Когда позицию никто не взял
           try:
               participantList.append([str(info_items[i][0]), info_urls[i][1]])
           except:
               participantList.append([str(info_items[i][0]), ''])
           i += 1

       return participantList
    
    def createTable(self, spId, namedRange, participants = 1, item = [], image = "https://i.pinimg.com/originals/50/d8/03/50d803bda6ba43aaa776d0e243f03e7b.png"):
        '''
        Создаёт и заполняет базовую таблицу по заданным параметрам

        :param spId: айди листа в таблице
        :param namedRange: имя Именованного диапозона
        :param participants: количество участников лота
        :param item:
        :param image: ссылка на изображение для оформления лота
        :return:
        '''
        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                  body={"requests": self.sp.prepareLot(self.getSheetListProperties(), spId, participants=participants, rangeName=namedRange)}).execute()

        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                           body=self.sp.prepareBody(spId, image, collect= namedRange, item = item)).execute()

    def updateTable(self, namedRange, request, topicUrl):
        '''
        Обновляет таблицу в соотвествии с информацией об участниках

        :param namedRange: имя Именованного диапозона
        :param request: словарь участников лота вида: {"participants": количество, "participantList": [[ строка_позиций, участник], ...] }
        :return:
        '''

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                  body={"requests": self.sp.updateBaseOfLot(self.getJsonNamedRange(namedRange), request["participants"])}).execute()

        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                           body=self.sp.updateBaseValues(self.getJsonNamedRange(namedRange),request["participantList"], topicUrl)).execute()

    def moveTable(self, sheetTo, namedRange):
        '''
        Перемещает таблицу на другое место

        :param sheetTo: айди листа, на который нужно переместить таблицу
        :param namedRange: имя Именованного диапозона
        :return:
        '''

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                  body={ "requests": self.sp.changeList(self.getSheetListProperties(), sheetTo, namedRange, self.getJsonNamedRange(namedRange))}).execute()

        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                           body=self.sp.setDateOfShipment(sheetTo, self.getJsonNamedRange(namedRange))).execute()

    def addRows(self, spId):
        '''
        Добавление строчек на лист
        :param spId: айди листа в таблице
        :return:
        '''

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                  body={"requests": [ce.updateSheetProperties(spId, 650)]}).execute()
        
    def deleteNamedRange(self, namedRange):
        '''
   
        :param spId: айди листа в таблице
        :return:
        '''

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                  body={"requests": [ce.deleteNamedRange(name = namedRange)]}).execute()


    def makeItemString(self, items):
        '''
        Создаёт упорядоченную по номерам позций строку айтомов
        :param items: массив айтемов
        :return: возвращает строку
        '''

        try:
            items = [int(item) for item in items]

        except:
            items = items[1:]
            items = [int(item) for item in items]

        items.sort()
        itemString = (''.join([str(item) + ', ' for item in items]))[0:-2]

        return itemString


    def getTopicUrl(self, namedRange):
        '''
        Получение ссылки из обсуждения на конкретный лот
        :param namedRange: имя Именованного диапозона
        :return: строка со ссылкой
        '''

        topicUrl = self.getJsonNamedRange(namedRange, typeCalling=1)['values'][2][-1]
        topicUrl = re.findall('"(\S+)"', topicUrl)[0]

        return topicUrl


    def changePositions(self, namedRange, newParticipants, payed):
        '''
        Производит автоматическую перепись позиций для участников лота (новые участники включаются)
        :param spId: айди листа в таблице
        :param namedRange: имя Именованного диапозона
        :param newParticipants: список участников и их новых позиций в формате [[ строка_позиций, участник], ...]
        :return:
        '''


        # информация об участниках, позициях и оплатах хранится как:
        # participant = [ ['позиции через запятую', 'Гиперссылка на участника'], [ [сумма, оплат, участника], [цвета, каждой, колонки] ]
        # работа в основном по participant[0]. Остальное дополнительная информация

        colors = [c.light_red, c.light_green]

        newParticipantColor = colors[payed]
        newPayment = [newParticipantColor for i in range(5)]

        oldParticipants = concatList(self.getParticipantsList(namedRange), self.getPaymentAmount(namedRange))
        actualParticipants = []
        activeIndexes = set()

        # доставка в РФ может быть не выставлена
        whiteCount = [x[1][1][2] for x in oldParticipants].count(c.white)
        if len(oldParticipants) == whiteCount:
            newPayment[2] = c.white
            newPayment[3] = c.white

        paymentNew = []
        for new in newParticipants:
            paymentNew.append([['' for i in range(5)], newPayment])
        newParticipants = concatList(newParticipants, paymentNew)

        # связка хохяин - индекс
        #oldParticipantsNoItems = {part[1]: oldParticipants.index(part) for part in oldParticipants}
        actualParticipantsNoItems = {part[0][1]: actualParticipants.index(part) for part in actualParticipants}

        for new in newParticipants:

            newItems = new[0][0].split(', ')

            for i in range(len(oldParticipants)):

               oldItems = oldParticipants[i][0][0].split(', ')

               for newItem in newItems:
                  if newItem in oldItems:

                       if len(oldParticipants[i][0][0]) >= 1:
                            oldItems.remove(newItem)
                            oldParticipants[i][0][0] = self.makeItemString(oldItems)

                            if oldParticipants[i][0][1] in actualParticipantsNoItems.keys():
                               index = actualParticipantsNoItems[oldParticipants[i][0][1]]
                               actualParticipants[index][0][0] = oldParticipants[i][0][0]

                            else:
                                actualParticipants.append(oldParticipants[i])

                       activeIndexes.add(i)

            # связка хохяин - индекс
            oldParticipantsNoItems = {part[0][1]: oldParticipants.index(part) for part in oldParticipants}
            actualParticipantsNoItems = {part[0][1]: actualParticipants.index(part) for part in actualParticipants}

            # заполняем данными человека, которому уступили

            if new[0][1] in oldParticipantsNoItems.keys():
                index = oldParticipantsNoItems[new[0][1]]
                itemList = oldParticipants[index][0][0].split(', ')
                itemList.extend(newItems)
                activeIndexes.add(index)
            else:
                itemList = newItems


            if new[0][1] in actualParticipantsNoItems.keys():
                index = actualParticipantsNoItems[new[0][1]]
                actualParticipants[index][0][0] = self.makeItemString(itemList)
            else:
                actualParticipants.append([[self.makeItemString(itemList), new[0][1]], [['' for i in range(5)], newPayment]])

        # позиции тех, у которых ничего неизменилось
        inactiveIndexes = set([i for i in range(len(oldParticipants))]) - activeIndexes
        inactiveParticipants = [oldParticipants[i] for i in inactiveIndexes]

        actualParticipants.extend(inactiveParticipants)

        # зачистка от пустых позиций
        act = actualParticipants.copy()
        for i in range(len(actualParticipants)):
            if len(actualParticipants[i][0][0]) == 0:
                act.remove(actualParticipants[i])
        actualParticipants = act

        actualParticipants.sort(key=lambda x: x[0][0].find(',') > 0 and int(x[0][0][0:x[0][0].find(',')]) or int(x[0][0][0:len(x[0][0])]))

        paymentAmount = [x[1][0] for x in actualParticipants]
        paymentInfo = [x[1][1] for x in actualParticipants]
        actualParticipants = [x[0] for x in actualParticipants]

        request = { "participants": {"amount": len(actualParticipants), "paymentInfo": paymentInfo
                                    },
                    "participantList": actualParticipants
        }

        additionalInfo = { "payment": paymentAmount}


        self.updateTable(namedRange, request, additionalInfo["payment"])

        # инфа об платах для обновления комментария в обсуждении
        paymentInfo = self.getPaymentStatus(namedRange)

        return actualParticipants, paymentInfo


    def replaceOldUrls(self, namedRange):
        '''
        Автозамена старого формата ссылок на новый
        :param namedRange:
        :return:
        '''

        urlList = self.getOldUrls(namedRange)
        range_ = self.getJsonNamedRange(namedRange)

        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                           body=self.sp.replaceOldUrls(range_, urlList)).execute()