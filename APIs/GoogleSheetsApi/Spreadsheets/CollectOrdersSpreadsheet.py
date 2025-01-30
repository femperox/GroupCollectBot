import APIs.GoogleSheetsApi.API.Cells_Editor as ce
from APIs.GoogleSheetsApi.API.Styles.Borders import Borders as b
from APIs.GoogleSheetsApi.API.Styles.Colors import Colors as c
import re
from pprint import pprint
from dateutil.relativedelta import *
from multipledispatch import dispatch
from confings.Consts import CollectOrdersSheetNames as sheetNames, ShipmentPriceType
from APIs.posredApi import PosredApi
from APIs.GoogleSheetsApi.API.Constants import ConditionType
from APIs.utils import getExpiryDateString

class CollectOrdersSpreadsheetClass():

    spreadsheetsIds = {}
    startLotRow = 0
    startParticipantRow = 0
    summaryRow = 0

    def __init__(self, sheetList):

        for i in range(len(sheetList)):
            self.spreadsheetsIds[sheetList[i]['properties']['title']] = (sheetList[i]['properties']['sheetId'], sheetList[i]['properties']['index'], sheetList[i]['properties']['title'])
        
        pprint(self.spreadsheetsIds)

    def findRowCount(self, sheetList, spId):
        '''
        Поиск суммарного количества строк на листе

        :param sheetList: Список свойств листов таблицы
        :param spId: айди листа в таблице
        :return: возвращает индекс последней строки
        '''

        name = self.findName(spId)
        properties = sheetList[self.spreadsheetsIds[name][1]]['properties']
        return properties['gridProperties']['rowCount']

    def findFreeRaw(self, sheetList, spId, namedRange = '', typeCalling = 1):
        '''
        Поиск свободной ячейки в таблице

        :param sheetList: Список свойств листов таблицы
        :param spId: айди листа в таблице
        :return: возвращает индекс свободной строки
        '''

        spIds = list(self.spreadsheetsIds.items())

        if namedRange.find("DCollect") == 0 or typeCalling == 1:
            startColumnIndex = 1
        else:
            startColumnIndex = 11

        sheetId = 0

        for i in range(len(spIds)):
            if spIds[i][1][0] == spId:
                sheetId = spIds[i][1][1]
                break

        # Поиск свободного места
        try:
            # Узнаём последнюю заполненную

            neededMerges = [merge for merge in sheetList[sheetId]['merges'] if merge['startColumnIndex'] == startColumnIndex]
            freeRaw = sorted(neededMerges, key=lambda x: x['endRowIndex'], reverse=True)[0]['endRowIndex']
            return freeRaw+3
        except:
            return 1

    def findName(self, spId):
        '''
        Поиск имени листа по его айди

        :param spId: айди листа в таблице
        :return: возвращает строчку-имя
        '''

        spItems = list(self.spreadsheetsIds.items())

        for i in range(len(spItems)):
            if spItems[i][1][0] == spId:
                return spItems[i][0]


    def prepareLot(self, sheetList, spId, participants = 1, rangeName = ""):
        '''
        подготовка json запроса для создания таблицы лота

        :param sheetList: Список свойств листов таблицы
        :param spId: айди листа в таблице
        :param participants: количество участников лота
        :return: возвращает json запрос
        '''

        request = []
        self.startLotRow = self.findFreeRaw(sheetList, spId)
        self.startParticipantRow = self.startLotRow + 14
        self.summaryRow = self.startParticipantRow + participants

        if self.summaryRow >= self.findRowCount(sheetList, spId):
            request.append(ce.updateSheetProperties(spId, addingRows = 500))

        # стили ячеек
        request.append(ce.repeatCells(spId, "A{0}:H{1}".format(self.startLotRow, self.summaryRow), c.white))
        request.append(ce.repeatCells(spId, "I{0}:I{1}".format(self.startLotRow, self.startLotRow + 4), c.white, hali = "RIGHT"))
        request.append(ce.repeatCells(spId, "J{0}:J{1}".format(self.startLotRow, self.startLotRow + 4), c.white))
        request.append(ce.repeatCells(spId, "C{0}:C{0}".format(self.startLotRow), c.light_purple))
        request.append(ce.repeatCells(spId, "A{0}:B{0}".format(self.startLotRow), c.light_purple, hali = "RIGHT"))
        request.append(ce.repeatCells(spId, "A{0}:C{0}".format(self.summaryRow), c.light_purple, hali = "RIGHT"))
        request.append(ce.repeatCells(spId, "D{0}:G{0}".format(self.summaryRow), c.light_purple))
        request.append(ce.repeatCells(spId, "J{0}:J{0}".format(self.startLotRow+12), c.light_yellow, hali = "RIGHT", textFormat = "False"))

        # объдинение ячеек
        request.append(ce.mergeCells(spId, "A{0}:B{0}".format(self.startLotRow)))
        request.append(ce.mergeCells(spId, "D{0}:D{1}".format(self.startLotRow, self.startLotRow+13)))
        request.append(ce.mergeCells(spId, "E{0}:E{1}".format(self.startLotRow, self.startLotRow+13)))
        request.append(ce.mergeCells(spId, "F{0}:F{1}".format(self.startLotRow, self.startLotRow+13)))
        request.append(ce.mergeCells(spId, "G{0}:G{1}".format(self.startLotRow, self.startLotRow+13)))
        request.append(ce.mergeCells(spId, "H{0}:H{1}".format(self.startLotRow, self.startLotRow + 13)))
        request.append(ce.mergeCells(spId, "A{0}:C{1}".format(self.startLotRow+1, self.startLotRow+13)))  # место для картинки
        request.append(ce.mergeCells(spId, "A{0}:C{0}".format(self.summaryRow))) # для "суммарно"

        for i in range(participants):
            request.append(ce.mergeCells(spId, "B{0}:C{0}".format(self.startParticipantRow+i)))
            request.append(ce.repeatCells(spId, "D{0}:E{0}".format(self.startParticipantRow+i), c.light_red))
        
        # условное форматирование            
        endParticipantRow = self.startParticipantRow + participants - 1
        request.append(ce.addConditionalFormatRuleColorChange(spId, f"H{self.startParticipantRow}:H{endParticipantRow}", ConditionType.NUMBER_LESS_THAN_EQ, "0", c.light_green))
        request.append(ce.addConditionalFormatRuleColorChange(spId, f"H{self.startParticipantRow}:H{endParticipantRow}", ConditionType.NUMBER_GREATER, "0", c.light_red))

        # границы ячеек
        request.append(ce.setCellBorder(spId, "A{0}:H{1}".format(self.startLotRow, self.summaryRow), bstyleList=b.plain_black))
        request.append(ce.setCellBorder(spId, "I{0}:J{1}".format(self.startLotRow, self.startLotRow+4), bstyleList=b.plain_black))
        request.append(ce.setCellBorder(spId, "I{0}:J{1}".format(self.startLotRow+5, self.summaryRow), only_outer= True, bstyleList=b.plain_black))

        request.append(ce.addNamedRange(spId, "A{0}:J{1}".format(self.startLotRow, self.summaryRow), rangeName))

        return request

    def defineCollectType(self, collect):
        '''
        Определяет тип коллективки. Т.е. её номер и (коллективка/индивидуалка)

        :param collect: название именованного диапозона
        :return: возвращает тип коллекта и его номер
        '''

        try:
            collectType, collectNum = re.split(r"\d", collect, 1)
            collectNum = collect[len(collectType)] + collectNum
        except:
            collectType = collect
            collectNum = 0
        collectType = "Коллективка" if collectType.find("Collect")>=0 else "Индивидуалка"

        return collectType, collectNum


    def prepareValues(self, spId, image, collect = "", item = []):
        '''
        подготовка блока data в json-запросе для заполнения таблицы значениями

        :param spId: айди листа в таблице
        :param collect: название именованного диапозона
        :return: возвращает часть json запроса
        '''

        collectType, collectNum = self.defineCollectType(collect)

        data = []

        participants = self.summaryRow - self.startParticipantRow


        sheetTitle = self.findName(spId)

        ran = sheetTitle +"!A{0}:B{0}".format(self.startLotRow)
        data.append(ce.insertValue(spId, ran, "{1} №{0}   Трек:".format(collectNum, collectType)))

        words = ["Позиция (с налогом)", "Доставка по Япе", "Доставка до склада посреда в транзит стране", "Доставка до коллективщика", "Задолжность",
                "Вес лота:", "Беседа лота:", "Лот в обсуждении:", "Ссылка на сайте:", "Номер у посреда:","СУММАРНО"]
        mergedWordsAm = 5
        unmergedWordsAm = len(words) - mergedWordsAm

        # Имена шапок по оплатам и задание формулы суммы
        for i in range(mergedWordsAm):
            letter = chr(i + 3 + ord('a'))
            ran = sheetTitle +"!{0}{1}".format(letter, self.startLotRow)
            data.append(ce.insertValue(spId, ran, words[i]))

            ran = sheetTitle + "!{0}{1}".format(letter, self.summaryRow)
            if letter == 'h':
                formula = "=SUM(D{0}:G{0})".format(self.summaryRow)
            else:
                formula = "=SUM({0}{1}:{0}{2})".format(letter, self.startParticipantRow, self.summaryRow-1)
            data.append(ce.insertValue(spId, ran, formula))

        # Имена шапок инфы о лоте
        for i in range(unmergedWordsAm-1):
            ran = sheetTitle + "!I{0}".format(self.startLotRow+i)
            data.append(ce.insertValue(spId, ran, words[mergedWordsAm+i]))

        # Нумерация участников и задание формулы задолжности
        for i in range(participants):
            ran = sheetTitle + "!A{0}".format(self.startParticipantRow+i)
            data.append(ce.insertValue(spId, ran, i+1))

            ran = ran.replace('A', 'H', 1)
            data.append(ce.insertValue(spId, ran, "=D{0}+E{0}".format(self.startParticipantRow+i)))

        # Имена шапки "суммарно"
        ran = sheetTitle + "!A{0}".format(self.summaryRow)
        data.append(ce.insertValue(spId, ran, words[-1]))

        # Изображение лота
        ran = sheetTitle + "!A{0}".format(self.startLotRow+1)
        image = '=IMAGE("{0}")'.format(image)
        data.append(ce.insertValue(spId, ran, image))

        # информация о сайте
        url = f'=HYPERLINK("{item["page"]}"; "{item["siteName"]}")'
        ran = sheetTitle + "!J{0}".format(self.startLotRow+3)
        data.append(ce.insertValue(spId, ran, url))

        # Для расчётов

        # Курс
        form = "!J{0}"
        ran = sheetTitle + form.format(self.startLotRow+5)
        formula = f"={str(PosredApi.getCurrentCurrencyRateByUrl(url = item['page'])).replace('.', ',')}"
        data.append(ce.insertValue(spId, ran, formula))

        for i in range(2):
            row = self.startLotRow+7+i
            ran = sheetTitle + form.format(row)
            formula = "=CEILING(I{0}*J{1})".format(row, self.startLotRow+5)
            data.append(ce.insertValue(spId, ran, formula))

            ran = sheetTitle + "!I{0}".format(row)
            data.append(ce.insertValue(spId, ran, 0))

        for i in range(ord('I'), ord('J')+1):
            row = self.startLotRow + 9
            ran = sheetTitle + "!{0}{1}".format(chr(i), row)
            formula = "= {0}{1} + {0}{2}".format(chr(i), row - 2, row -1)
            data.append(ce.insertValue(spId,ran,formula))

        
        if item:
            # стоимость лота со всеми комм и дост
            ran = sheetTitle + "!I{0}".format(self.startLotRow+7)
            tax = item['tax']/100 if item['tax'] > 0 else 0
            formula = "={0} + {0}*{1} + {2} + {0}*0.15".format(item['itemPrice'], tax, item['posredCommission']).replace('.', ',')
            data.append(ce.insertValue(spId, ran, formula))

            ran = sheetTitle + "!I{0}".format(self.startLotRow+8)
            shipmentPrice = item['shipmentPrice'].value if isinstance(item['shipmentPrice'], ShipmentPriceType) else item['shipmentPrice']
        
            formula = f"={shipmentPrice}".replace('.', ',')
            data.append(ce.insertValue(spId, ran, formula))
            
        
            # личная комм
            ran = sheetTitle + "!I{0}".format(self.startLotRow+11)            
            formula = "={0} + {0}*{1} + {2}".format(item['itemPrice'], tax, item['posredCommission']).replace('.', ',')
            data.append(ce.insertValue(spId, ran, formula))
        
            formula = "=CEILING(I{0}*J{1})".format(self.startLotRow+11, self.startLotRow+5)
            data.append(ce.insertValue(spId, ran.replace('I', 'J'), formula))
        
            # суммарная прибыль с лота
            ran = sheetTitle + "!J{0}".format(self.startLotRow+12)
            formula = "=J{0} - J{1}".format(self.startLotRow + 7, self.startLotRow+11)
            data.append(ce.insertValue(spId, ran, formula))

        if participants == 1:
            ran = sheetTitle + "!D{0}".format(self.startParticipantRow)
            formula = "=J{0}".format(self.startLotRow+7)
            data.append(ce.insertValue(spId, ran, formula))
            ran = sheetTitle + "!E{0}".format(self.startParticipantRow)
            formula = "=J{0}".format(self.startLotRow + 8)
            data.append(ce.insertValue(spId, ran, formula))

        return data



    def prepareBody(self, spId, image, collect = "", item = []):
        '''
        подготовка json запроса для заполнения таблицы лота информауией

        :param spId: айди листа в таблице
        :param collect: название именованного диапозона
        :return: возвращает json запрос
        '''

        body = {}
        body["valueInputOption"] = "USER_ENTERED"
        body["data"] = self.prepareValues(spId, image, collect, item)

        return body


    def changeList(self, sheetList, newSpId, collectId, collectNamedRange):
        '''
        Перемещение таблицы с одного листа на другой

        :param sheetList: Список свойств листов таблицы
        :param newSpId: айди листа в таблице, куда нужно перенести таблицу
        :param collectId: имя именованного диапозона, совпадающего с именем коллективки
        :param collectNamedRange: именованный диапозон в формате "В1:С45" - пример
        :return: возвращает json запрос
        '''

        if collectId.find("DCollect") == 0:
            startLetter = 'A'
            endLetter = 'J'
        else:
            startLetter = 'L'
            endLetter = 'U'

        freeRow = self.findFreeRaw(sheetList, newSpId, collectId, typeCalling = 0)
        newRange = "{0}{1}".format(startLetter, freeRow)

        oldSheetTitle, oldRange = collectNamedRange.split("!")

        index = re.findall('(\d+)', oldRange)


        try:
            oldSheetTitle = re.findall("'(.+)'", oldSheetTitle)[0]
        except:
            pass
        oldSpId = self.spreadsheetsIds[oldSheetTitle][0]

        request = []

        # проверка на возможность вставки
        newEnd = int(index[1]) - int(index[0]) + freeRow
        if newEnd >= self.findRowCount(sheetList, newSpId):
            request.append(ce.updateSheetProperties(newSpId, addingRows = 500))

        request.append(ce.CutPasteRange(oldSpId, oldRange, newRange, newSpId))
        request.append(ce.deleteNamedRange(collectId))

        convertedRange = oldRange.split(":")

        # Удаляем со старого места таблицу и пустую строку под ней
        oldRangeWithBlankRow = convertedRange[0] +":" + convertedRange[1][0] + str( int(convertedRange[1][1:])+1)
        request.append(ce.deleteRange(oldSpId, oldRangeWithBlankRow))

        # оформелние ячеек с датами отправок
        request.append(ce.repeatCells(newSpId, "{0}{1}:{0}{1}".format(endLetter, newEnd), c.white_blue, hali="LEFT"))
        request.append(ce.repeatCells(newSpId, "{0}{1}:{0}{1}".format(chr(ord(endLetter)-1), newEnd), c.white_blue, hali="RIGHT"))
        request.append(ce.setCellBorder(newSpId, "{0}{1}:{2}{1}".format(chr(ord(endLetter)-1), newEnd, endLetter), all_same= False, bstyleList=[b.no_border, b.plain_black, b.plain_black, b.plain_black]))

        convertedRange = int(convertedRange[1][1:]) - int(convertedRange[0][1:]) + int(newRange[1:])
        newRange += ':{0}{1}'.format(endLetter, convertedRange)
        request.append(ce.addNamedRange(newSpId, newRange, collectId))


        return request

    def setDateOfShipment(self, spId, namedRange):

        '''
        Ставит ячейку даты

        :param spId:
        :param namedRange: имя Именованного диапозона
        :return:
        '''

        data = []

        print(namedRange)

        if spId == self.spreadsheetsIds[sheetNames.collectArchive][0]:
            info = getExpiryDateString()
            label = 'Получено - Забрать:'
        else:
            info = ''
            label = 'Отправлено'

        sheetTitle, index = namedRange.split("!")
        lastLetter = index.split(':')[1]
        lastLetter = re.findall('(\D+)', lastLetter)[0]

        indexes = re.findall('(\d+)', index)

        ran = sheetTitle + "!{0}{1}:{0}{1}".format(lastLetter, indexes[1])
        data.append(ce.insertValue(spId, ran, info))
        ran = sheetTitle + "!{0}{1}:{0}{1}".format(chr(ord(lastLetter)-1), indexes[1])
        data.append(ce.insertValue(spId, ran, label))

        body = {}
        body["valueInputOption"] = "USER_ENTERED"
        body["data"] = data


        return body


    @dispatch(str, int)
    def updateBaseOfLot(self, collectNamedRange, participants:int):
        '''
        Обновление таблицы в соотвествии с количеством участников коллективки

        :param collectNamedRange: именованный диапозон в формате "В1:С45" - пример
        :param participants: количество участников
        :return: возвращает json запрос
        '''

        request = []

        sheetTitle, range_ = collectNamedRange.split("!")

        try:
            spId = self.spreadsheetsIds[sheetTitle[1:len(sheetTitle)-1]][0]
        except:
            spId = self.spreadsheetsIds[sheetTitle][0]

        range_ = range_.split(":")

        self.startParticipantRow = int(range_[0][1:]) + 14
        startLetter = range_[0][0]
        endLetter = range_[1][0]

        rowsAmount = int(range_[1][1:]) - self.startParticipantRow

        if participants <= rowsAmount:
            rangeToDelete = "{2}{0}:{3}{1}".format(self.startParticipantRow + participants, int(range_[1][1:])-1, startLetter, endLetter )
            request.append(ce.deleteRange(spId, rangeToDelete))
        else:
            difference = participants - rowsAmount
            rangeToAdd = '{2}{0}:{3}{1}'.format(self.startParticipantRow+1, self.startParticipantRow+difference, startLetter, endLetter)
            request.append(ce.insertRange(spId, rangeToAdd))

            mCell1 = chr(ord(startLetter)+1)
            mCell2 = chr(ord(startLetter)+2)

            for i in range(difference):
                request.append(ce.mergeCells(spId, "{1}{0}:{2}{0}".format(self.startParticipantRow+1+i , mCell1, mCell2)))

        return request

    @dispatch(str, dict)
    def updateBaseOfLot(self, collectNamedRange, additionalInfo:dict):

        request = self.updateBaseOfLot(collectNamedRange, additionalInfo['amount'])

        sheetTitle, range_ = collectNamedRange.split("!")

        try:
            spId = self.spreadsheetsIds[sheetTitle[1:len(sheetTitle) - 1]][0]
        except:
            spId = self.spreadsheetsIds[sheetTitle][0]

        range_ = range_.split(":")

        self.startParticipantRow = int(range_[0][1:]) + 14
        startLetter = range_[0][0]
        endLetter = range_[1][0]

        rowsAmount = int(range_[1][1:]) - self.startParticipantRow

        paymentCells = [chr(ord(startLetter) + 3 + i) for i in range(5)]

        for i in range(len(additionalInfo["paymentInfo"])):
            for j in range(len(additionalInfo["paymentInfo"][i])):

                range_ = "{0}{1}:{0}{1}".format(paymentCells[j], self.startParticipantRow+i)
                request.append(ce.repeatCells(spId, range_, additionalInfo["paymentInfo"][i][j]))
                request.append(ce.setCellBorder(spId, range_, only_outer=True, bstyleList=b.plain_black))

        return request

    def listToString(self, list):
        '''
        Переводит список в строчку в формате "x, y, z"

        :param list: список
        :return: возвращает строку
        '''

        itemString = ""

        for i in range(len(list)):
            itemString += str(list[i])+", "

        return itemString[:-2]

    @dispatch(str, list, str)
    def updateBaseValues(self, collectNamedRange, participantsInfo, topicUrl:str):
        '''
        Обновляет значения ячеек: позиции, участники

        :param collectNamedRange: именованный диапозон в формате "В1:С45" - пример
        :param participantsInfo: список с инфой об участнике и его позициях
        :return: возвращает json запрос
        '''

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []

        sheetTitle, range_ = collectNamedRange.split("!")
        range_ = range_.split(":")
        startLetter = range_[0][0]
        nameCell = chr(ord(startLetter)+1)
        endLetter = range_[1][0]
        try:
            spId = self.spreadsheetsIds[sheetTitle[1:len(sheetTitle) - 1]][0]
        except:
            spId = self.spreadsheetsIds[sheetTitle][0]

        for i in range(len(participantsInfo)):

            ran = sheetTitle + "!{1}{0}".format(self.startParticipantRow+i ,startLetter)

            if isinstance(participantsInfo[i][0], str):
                info = participantsInfo[i][0]
            else: info = self.listToString(participantsInfo[i][0])

            data.append(ce.insertValue(spId, ran, info ) )
            ran = ran.replace(startLetter, nameCell, 1)

            data.append(ce.insertValue(spId, ran, participantsInfo[i][1] ) )

        topicUrl = '=HYPERLINK("{0}"; "тык")'.format(topicUrl)
        ran = sheetTitle + "!{1}{0}".format(self.startLotRow+2, endLetter)
        data.append(ce.insertValue(spId, ran, topicUrl))

        body["data"] = data
        return body

    @dispatch(str, list, list)
    def updateBaseValues(self, collectNamedRange, participantsInfo, additionalInfo:list):
        '''
        Обновляет значения ячеек: позиции, участники, суммы оплат

        :param collectNamedRange: именованный диапозон в формате "В1:С45" - пример
        :param participantsInfo: список с инфой об участнике и его позициях
        :param additionalInfo: список с инфой о суммах оплат участников
        :return: возвращает json запрос
        '''
        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []

        sheetTitle, range_ = collectNamedRange.split("!")
        range_ = range_.split(":")
        startLetter = range_[0][0]
        nameCell = chr(ord(startLetter) + 1)
        endLetter = range_[1][0]

        paymentCells = [chr(ord(nameCell)+2+i) for i in range(5)]

        try:
            spId = self.spreadsheetsIds[sheetTitle[1:len(sheetTitle) - 1]][0]
        except:
            spId = self.spreadsheetsIds[sheetTitle][0]

        for i in range(len(participantsInfo)):

            ran = sheetTitle + "!{1}{0}".format(self.startParticipantRow + i, startLetter)

            if isinstance(participantsInfo[i][0], str):
                info = participantsInfo[i][0]
            else:
                info = self.listToString(participantsInfo[i][0])

            data.append(ce.insertValue(spId, ran, info))
            ran = ran.replace(startLetter, nameCell, 1)

            data.append(ce.insertValue(spId, ran, participantsInfo[i][1]))

            # сумма оплат каждого участника
            for j in range(len(additionalInfo[i])):
                ran = sheetTitle + "!{1}{0}".format(self.startParticipantRow + i, paymentCells[j])
                data.append(ce.insertValue(spId, ran, additionalInfo[i][j]))

        body["data"] = data
        return body

    def replaceOldUrls(self, collectNamedRange, urlList):
        '''
        Обновляет ссылки на участников

        :param collectNamedRange:
        :param urlList:
        :return:
        '''

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []

        sheetTitle, range_ = collectNamedRange.split("!")
        range_ = range_.split(":")
        startParticipantRow = int(range_[0][1:]) + 14
        nameCell = chr(ord(range_[0][0]) + 1)

        try:
            spId = self.spreadsheetsIds[sheetTitle[1:len(sheetTitle) - 1]][0]
        except:
            spId = self.spreadsheetsIds[sheetTitle][0]

        for i in range(len(urlList)):

            if len(urlList[i]) == 0:
                continue
            ran = sheetTitle + "!{1}{0}".format(startParticipantRow + i, nameCell)
            info = f'=HYPERLINK("{urlList[i][1]}"; "{urlList[i][0]}")'
            data.append(ce.insertValue(spId, ran, info))

        body["data"] = data
        return body
    

    def checkDeliveryToParticipant(self, rowInfo, participantList):
        """Проверить статус отправки позиций пользователя к нему

        Args:
            rowInfo (list): информация о строках
            participant_list (list): текущий список участников

        Returns:
            list of dict: статус отправки позиций пользователя к нему - стоит ли в очереди, отправлено ли
        """

        delivery_status_list = []
        for participant in participantList:

            for row in rowInfo:
                if 'hyperlink' in row['values'][1] and row['values'][1]['hyperlink'].find(str(participant)) > -1:
                    is_sent = False
                    is_in_queue = False
                    is_in_queue = row['values'][0]['userEnteredFormat']['backgroundColor'] == c.dark_pink
                    if is_in_queue:
                        is_sent = row['values'][1]['userEnteredFormat']['backgroundColor'] == c.dark_pink
                    
                    delivery_status_list.append({'user': participant, 'is_in_queue': is_in_queue, 'is_sent': is_sent})
                    

        return delivery_status_list





