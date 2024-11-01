import APIs.GoogleSheetsApi.API.Cells_Editor as ce
from APIs.GoogleSheetsApi.API.Styles.Borders import Borders as b
from APIs.GoogleSheetsApi.API.Styles.Colors import Colors as c
from APIs.GoogleSheetsApi.API.Constants import ConditionType
from confings.Consts import OrderTypes
from APIs.utils import getExpiryDateString
from APIs.posredApi import PosredApi
from APIs.utils import getChar
from pprint import pprint

class StoresCollectOrdersList:

    def __init__(self):

        self.startRow = 1
        self.endRow = 14
        self.participantRowStart = self.endRow + 1

    def setColumns(self, order_type):
        """Проставить базовые значения колонок

        Args:
            order_type (OrderTypes): тип закупки.
        """

        self.priceColumn = 'D'
        self.firstPaymentColumn = getChar(self.priceColumn, 2)

        if order_type == OrderTypes.jp:
            self.endColumn = 'I'
        elif order_type in [OrderTypes.us, OrderTypes.eur]:
            self.endColumn = 'H'
        elif order_type == OrderTypes.ami:
            self.endColumn = 'L' 
            self.priceColumn = 'E'
            self.firstPaymentColumn = 'J'


    def prepareTable(self, list_id, participant_count = 1, order_type = OrderTypes.ami):
        """Подготовка таблицы. 

        Args:
            list_id (int): id листа
            participant_count (int, optional): количество участников. Defaults to 1.
            order_type (OrderTypes, optional): тип закупки. Defaults to OrderTypes.ami.

        Returns:
            list: список реквестов по оформлению таблицы
        """
        
        request = []
        self.participantRowEnd = self.participantRowStart + participant_count - 1
        self.participantCount = participant_count

        self.setColumns(order_type = order_type)

        request.append(ce.setRowHeight(list_id, {"start": self.startRow+3, "end": self.startRow+4}, height=50))

        # объдинение ячеек
        request.append(ce.mergeCells(list_id, f"A{self.startRow+1}:{self.endColumn}{self.endRow-1}"))
        request.append(ce.mergeCells(list_id, f"B{self.endRow}:C{self.endRow}"))
        request.append(ce.mergeCells(list_id, f"A{self.startRow}:B{self.startRow}"))

        # стили ячеек
        request.append(ce.repeatCells(list_id, f"A{self.startRow}:{getChar(self.endColumn, 2)}1000", c.white))
        request.append(ce.repeatCells(list_id, f"A{self.startRow}:B{self.startRow}", c.light_purple))
        request.append(ce.repeatCells(list_id, f"A{self.endRow}:{getChar(self.endColumn, -1)}{self.endRow}", c.light_purple))
        request.append(ce.repeatCells(list_id, f"{getChar(self.endColumn, -1)}{self.startRow}:{self.endColumn}{self.startRow}", c.light_purple))
        request.append(ce.repeatCells(list_id, f"{getChar(self.endColumn, 2)}{self.startRow+5}:{getChar(self.endColumn, 2)}{self.startRow+5}", c.light_purple))
        request.append(ce.repeatCells(list_id, f"{getChar(self.endColumn, 2)}{self.startRow+7}:{getChar(self.endColumn, 2)}{self.startRow+7}", c.light_purple))
        request.append(ce.repeatCells(list_id, f"{getChar(self.endColumn, 2)}{self.startRow+9}:{getChar(self.endColumn, 2)}{self.startRow+9}", c.light_purple))
        request.append(ce.repeatCells(list_id, f"{getChar(self.endColumn, 1)}{self.startRow}:{getChar(self.endColumn, 1)}{self.startRow+3}", hali = "RIGHT", color = c.white))
        request.append(ce.repeatCells(list_id, f"{self.endColumn}{self.endRow}:{self.endColumn}{self.endRow}", c.turquoise))
        request.append(ce.repeatCells(list_id, f"{getChar(self.priceColumn, 3)}{self.participantRowEnd+3}:{getChar(self.priceColumn, 3)}{self.participantRowEnd+3}", c.light_yellow, textFormat = "False"))

        for i in range(participant_count):
            request.append(ce.mergeCells(list_id, f"B{self.participantRowStart+i}:C{self.participantRowStart+i}"))
            request.append(ce.repeatCells(list_id, f"{getChar(self.priceColumn, 2)}{self.participantRowStart+i}:{getChar(self.priceColumn, 2)}{self.participantRowStart+i}", c.light_red))
            
        # условное форматирование            
        request.append(ce.addConditionalFormatRuleColorChange(list_id, f"{self.endColumn}{self.participantRowStart}:{self.endColumn}{self.participantRowEnd}", ConditionType.NUMBER_LESS_THAN_EQ, "0", c.light_green))
        request.append(ce.addConditionalFormatRuleColorChange(list_id, f"{self.endColumn}{self.participantRowStart}:{self.endColumn}{self.participantRowEnd}", ConditionType.NUMBER_GREATER, "0", c.light_red))

        # границы ячеек
        request.append(ce.setCellBorder(list_id, f"A{self.startRow}:B{self.startRow}", bstyleList=b.plain_black))
        request.append(ce.setCellBorder(list_id, f"{getChar(self.endColumn, -1)}{self.startRow}:{self.endColumn}{self.startRow}", bstyleList=b.plain_black))
        request.append(ce.setCellBorder(list_id, f"A{self.startRow+1}:{self.endColumn}{self.endRow}", bstyleList=b.plain_black))
        request.append(ce.setCellBorder(list_id, f"{getChar(self.endColumn, 1)}{self.startRow}:{getChar(self.endColumn, 2)}{self.startRow+2}", bstyleList=b.plain_black))
        request.append(ce.setCellBorder(list_id, f"{getChar(self.endColumn, 2)}{self.startRow+5}:{getChar(self.endColumn, 2)}{self.startRow+10}", bstyleList=b.plain_black))
        request.append(ce.setCellBorder(list_id, f"{self.priceColumn}{self.participantRowEnd+2}:{getChar(self.priceColumn, 3)}{self.participantRowEnd+3}", bstyleList=b.plain_black))
        request.append(ce.setCellBorder(list_id, f"A{self.participantRowStart}:{self.endColumn}{self.participantRowEnd}", bstyleList=b.plain_black))

        return request
    
    def prepareTableValues(self, list_id, list_title, topic_url, order_type = OrderTypes.ami):
        """Подготовка значений таблицы

        Args:
            list_id (int): id листа
            list_title (string): название листа
            topic_url (string): ссылка на обсуждение в вк
            order_type (OrderTypes, optional): тип закупки. Defaults to OrderTypes.ami.

        Returns:
            list: список реквестов по заполнению таблицы данными
        """

        body = {}
        body["valueInputOption"] = "USER_ENTERED"
        data = []

        valueRange = list_title + '!{0}{1}'

        headers = ["Позиция", "Человек"]
        if order_type == OrderTypes.jp:
            headers.extend(["Позиция в йенах", "Позиция со всеми коммишками и дост по Японии в йенах", "В рублях", 
                 "Доставка до склада посреда в транзите", "Доставка до коллективщика", "Задолжность"])
        elif order_type == OrderTypes.us:
            headers.extend(["Позиция в долларах", "Позиция со всеми коммишками и дост в США в долларах", 
                       "В рублях", "Доставка до коллективщика", "Задолжность"])
        elif order_type == OrderTypes.ami:
            headers.extend(["Предоплата", "Позиция в йенах", "Позиция в йенах с коммишками", "В рублях",
                       "Доставка йен", "Доставка до склада посреда в транзите", "Общее", "Доставка до коллективщика", "Задолжность"])

        for i in range(len(headers)):
            currentLetter = getChar('A', i) if i < 2 else getChar('A', i+1)
            data.append(ce.insertValue(list_id, valueRange.format(currentLetter, self.endRow), headers[i]))

        commision_headers = ['Сумма', 'Сумма с Коммисией',	'Моя Коммисия', 'В рублях']
        for i in range(len(commision_headers)):
            currentLetter = getChar(self.priceColumn, i)
            data.append(ce.insertValue(list_id, valueRange.format(currentLetter, self.participantRowEnd + 2), commision_headers[i]))

            if i < 2:
                formula = f"=SUM({currentLetter}{self.participantRowStart}:{currentLetter}{self.participantRowEnd})"
            elif i == 2:
                formula = f"={self.priceColumn}{self.participantRowEnd + 3} * 0,1"
            else:
                formula = f"=FLOOR({getChar(currentLetter, -1)}{self.participantRowEnd + 3} * {self.endColumn}{self.startRow})"
            data.append(ce.insertValue(list_id, valueRange.format(currentLetter, self.participantRowEnd + 3), formula))

        headers_info = ['Беседа:', 'В обсуждении:', 'Номер у посреда:']
        for i in range(len(headers_info)):
            currentLetter = getChar(self.endColumn, 1)
            data.append(ce.insertValue(list_id, valueRange.format(currentLetter, self.startRow + i), headers_info[i]))

        headers_order_info = ['Сумма заказа', 'Доставка', 'Кол-во участников']
        for i in range(len(headers_order_info)):
            currentLetter = getChar(self.endColumn, 2)
            data.append(ce.insertValue(list_id, valueRange.format(currentLetter, self.startRow + 5 + i*2), headers_order_info[i]))

        # Название
        data.append(ce.insertValue(list_id, valueRange.format('A', self.startRow), list_title))

        # Курс
        data.append(ce.insertValue(list_id, valueRange.format(getChar(self.endColumn, -1), self.startRow), 'Курс:'))
        data.append(ce.insertValue(list_id, valueRange.format(self.endColumn, self.startRow), 
                                   PosredApi.getCurrentCurrencyRateByOrderType(order_type = order_type)))
        
        # Ссылка на обсуждение
        data.append(ce.insertValue(list_id, valueRange.format(getChar(self.endColumn, 2), self.startRow + 1), f'=HYPERLINK("{topic_url}"; "тык")'))
        
        # Кол-во участников
        data.append(ce.insertValue(list_id, valueRange.format(getChar(self.endColumn, 2), self.startRow + 10), f'=COUNTA(B{self.participantRowStart}:C{self.participantRowEnd})'))

        # перевод в рубли, коммишка и задолжность
        for i in range(self.participantRowStart, self.participantRowEnd + 1):
            formula = f'= CEILING({getChar(self.priceColumn, 1)}{i}*${self.endColumn}${self.startRow})'
            data.append(ce.insertValue(list_id, valueRange.format(getChar(self.priceColumn, 2), i), formula))

            if order_type == OrderTypes.ami:
                formula = f'= {self.firstPaymentColumn}{i} - {getChar(self.priceColumn, -1)}{i}'           
            else:
                formula = f'= {self.firstPaymentColumn}{i}'
            data.append(ce.insertValue(list_id, valueRange.format(self.endColumn, i), formula))

            commission_formula = PosredApi.getCommissionForCollectOrder(order_type = order_type)
            if order_type == OrderTypes.us:
                commission_formula = commission_formula.format(f'{self.priceColumn}{i}', self.participantCount)
            else:
                commission_formula = commission_formula.format(f'{self.priceColumn}{i}')

            formula = f'= {self.priceColumn}{i} + ' + commission_formula
            data.append(ce.insertValue(list_id, valueRange.format(getChar(self.priceColumn, 1), i), formula))

        body["data"] = data
        return body
    
    def updateTable(self, list_id, participant_count_new, participant_count_old):
        """Обновить таблицу

        Args:
            list_id (int): id листа
            participant_count_new (int): текущее кол-во участников
            participant_count_old (int): старое кол-во участников

        Returns:
            list: список реквестов по оформлению таблицы
        """

        request = []

        if participant_count_new < participant_count_old:
            rangeToDelete = f"A{self.participantRowStart}:Z{self.participantRowStart + participant_count_new}"
            request.append(ce.deleteRange(list_id, rangeToDelete))
        elif participant_count_new > participant_count_old:
            difference = participant_count_new - participant_count_old
            rangeToAdd = f'A{self.participantRowStart+1}:Z{self.participantRowStart+difference}'
            request.append(ce.insertRange(list_id, rangeToAdd))

            for i in range(difference):
                request.append(ce.mergeCells(list_id, f"B{self.participantRowStart+i+1}:C{self.participantRowStart+i+1}"))

        return request
    
    def updateTableCopyPaste(self, list_id, participant_list_count):

        request = []

        rangeToCopy = f'E{self.participantRowStart + participant_list_count + 1}:M{self.participantRowStart + participant_list_count + 1}'
        rangeToPaste = 'E{0}:M{1}'

        for i in range(1, participant_list_count + 1):
            request.append(ce.copyPasteRange(spId = list_id, 
                                             range = rangeToCopy, 
                                             newRange = rangeToPaste.format(self.participantRowStart + i, self.participantRowStart + i)))

        return request
    
    def updateTableValues(self, list_id, list_title, participant_list, addingParticipantsFlag = False):
        """Обновить значения таблицы

        Args:
            list_id (int): id листа
            list_title (string): название листа
            participant_list (list): текущий список участников
            order_type (bool, optional): флаг добавления участников. Defaults to False.

        Returns:
            list: список реквестов по заполнению таблицы данными
        """

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []
        valueRange = list_title + '!{0}{1}'

        for i in range(len(participant_list)):
            row_step = addingParticipantsFlag + i
            data.append(ce.insertValue(list_id, valueRange.format('A', self.participantRowStart+row_step), participant_list[i]['items']))
            if participant_list[i]['user_url']:
                data.append(ce.insertValue(list_id, valueRange.format('B', self.participantRowStart+row_step), f'''=HYPERLINK("{participant_list[i]['user_url']}"; "{participant_list[i]['user_name']}")'''))
            else:
                data.append(ce.insertValue(list_id, valueRange.format('B', self.participantRowStart+row_step), participant_list[i]['user_name']))

        body["data"] = data
        return body
    
    def updateTableValuesAddingParticipants(self, list_id, list_title, participant_list):

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []
        valueRange = list_title + '!{0}{1}'

        for i in range(len(participant_list)):
            data.append(ce.insertValue(list_id, valueRange.format('A', self.participantRowStart+i+1), participant_list[i]['items']))
            if participant_list[i]['user_url']:
                data.append(ce.insertValue(list_id, valueRange.format('B', self.participantRowStart+i+1), f'''=HYPERLINK("{participant_list[i]['user_url']}"; "{participant_list[i]['user_name']}")'''))
            else:
                data.append(ce.insertValue(list_id, valueRange.format('B', self.participantRowStart+i+1), participant_list[i]['user_name']))

        body["data"] = data
        return body        
        
    
    def updateTableRecieved(self, list_id):
        """Обновить таблицу как полученную закупку

        Args:
            list_id (int): id листа

        Returns:
            list: список реквестов по оформлению таблицы
        """

        request = []

        request.append(ce.mergeCells(list_id, f"C{self.startRow}:D{self.startRow}"))
        request.append(ce.mergeCells(list_id, f"E{self.startRow}:F{self.startRow}"))
        request.append(ce.repeatCells(list_id, f"C{self.startRow}:F{self.startRow}", c.white_blue))

        return request
    
    def updateTableValuesRecieved(self, list_id, list_title):
        """Обновить значения в таблице как в полученной закупке

        Args:
            list_id (int): id листа
            list_title (string): название листа

        Returns:
            list: список реквестов по заполнению таблицы данными
        """

        body = {}
        body["valueInputOption"] = "USER_ENTERED"
        data = []
        valueRange = list_title + '!{0}{1}'

        label = 'Получено - Забрать:'
        expiry_date = getExpiryDateString()

        data.append(ce.insertValue(list_id, valueRange.format('C', self.startRow), label))
        data.append(ce.insertValue(list_id, valueRange.format('E', self.startRow), expiry_date))

        body["data"] = data
        return body