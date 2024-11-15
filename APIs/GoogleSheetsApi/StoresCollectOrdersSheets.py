
from APIs.GoogleSheetsApi.ParentSheetClass import ParentSheetClass
import re
import APIs.GoogleSheetsApi.API.Cells_Editor as ce
from APIs.GoogleSheetsApi.API.Styles.Borders import Borders as b
from APIs.GoogleSheetsApi.API.Styles.Colors import Colors as c
from APIs.GoogleSheetsApi.Spreadsheets.StoresCollectOrdersList import StoresCollectOrdersList
from confings.Consts import OrderTypes, SHEETS_ID_FILE
from APIs.utils import concatList, getCurrentMonthString
from pprint import pprint
from datetime import datetime
import json

class StoresCollectOrdersSheets(ParentSheetClass):
    
    def __init__(self):

        super().__init__()
        self.setSpreadsheetId("storesCollectList")
        self.current_list = StoresCollectOrdersList()

    def archiveStoreCollect(self, list_id):
        """Перенести закупку в архив

        Args:
            list_id (int): id листа

        Returns:
            dict: словарь с id нового документа и нового листа
        """

        archive_spreadsheet_id = json.load(open(SHEETS_ID_FILE, encoding='utf-8'))['storesCollectArchiveList']

        new_list_id = self.copySheetListTo(sheet_id = list_id, new_spreadsheet_id = archive_spreadsheet_id)['sheetId']

        self.deleteSheetList(sheet_id = list_id)

        return {'new_sp_id': archive_spreadsheet_id, 'new_list_id': new_list_id}

    def createNewStoresCollect(self, title, topic_url, participant_count, order_type = OrderTypes.ami):
        """Создать лист закупки

        Args:
            title (string): название листа
            topic_url (string): ссылка на обсуждение в вк
            participant_count (int): количество участников
            order_type (OrderTypes, optional): тип закупки. Defaults to OrderTypes.ami.

        Returns:
            int: id листа
        """
        list_title = title
        if order_type != OrderTypes.ami:
            list_title += ' ' + getCurrentMonthString()

        list_id = self.createSheetList(title = list_title)
        
        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                body={"requests": self.current_list.prepareTable(list_id=list_id, 
                                                                                                 participant_count = participant_count,
                                                                                                 order_type = order_type)}).execute()
        
        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                    body = self.current_list.prepareTableValues(list_id = list_id,
                                                                                                list_title = list_title,
                                                                                                topic_url = topic_url,
                                                                                                order_type = order_type)).execute()
        return list_id

    def updateStoresCollect(self, list_id, participant_list, participant_count_old):
        """Обновить закупку

        Args:
            list_id (int): id листа
            participant_list (list): текущий список участников
            participant_count_old (int): старое кол-во участников
        """

        list_title = self.getSheetListName(sheet_id = list_id)

        request = self.current_list.updateTable(list_id = list_id, 
                                                participant_count_new = len(participant_list),
                                                participant_count_old = participant_count_old)
        if request:
            self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                    body={"requests": request}).execute()

        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                         body=self.current_list.updateTableValues(list_id = list_id,
                                                                                                  list_title = list_title,
                                                                                                  participant_list = participant_list)).execute()

    def addParticipants(self, list_id, new_participant_list, participant_count_old):

        list_title = self.getSheetListName(sheet_id = list_id)

        request = self.current_list.updateTable(list_id = list_id, 
                                                participant_count_new = len(new_participant_list) + participant_count_old,
                                                participant_count_old = participant_count_old)
        if request:
            request.extend(self.current_list.updateTableCopyPaste(list_id = list_id, participant_list_count = len(new_participant_list)))
            self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                    body={"requests": request}).execute()
            
        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                         body=self.current_list.updateTableValues(list_id = list_id,
                                                                                                  list_title = list_title,
                                                                                                  participant_list = new_participant_list,
                                                                                                  addingParticipantsFlag = True)).execute()
    def setStoresCollectRecieved(self, list_id):
        """Установить закупку полученной

        Args:
            list_id (int): id листа
        """

        list_title = f'{self.getSheetListName(sheet_id = list_id)} (ПРИЕХАЛО)'
        
        self.renameSheetList(sheet_id = list_id, title = list_title)

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                body={"requests": self.current_list.updateTableRecieved(list_id=list_id)}).execute()

        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                         body=self.current_list.updateTableValuesRecieved(list_id = list_id,
                                                                                                          list_title = list_title)).execute()

        self.changeSheetListIndex(sheet_id = list_id, new_index = len(self.get_sheets()))

    def updateParticipantItems(self, list_id, participant_list):
        """Обновить список позиций участника

        Args:
            list_id (int): id листа
            participant_list (list): текущий список участников
        """

        list_title = self.getSheetListName(sheet_id = list_id)

        rowInfo = self.getJsonNamedRange(f'{list_title}!A1:Z999', typeCalling=1)['values']

        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                         body=self.current_list.updateParticipantItemsValue(list_id = list_id,
                                                                                                            list_title = list_title,
                                                                                                            participant_list = participant_list,
                                                                                                            rowInfo = rowInfo)).execute()

    def checkDeliveryToParticipants(self, list_id, participantList):
        """Проверить статус отправки позиций пользователя к нему

        Args:
            list_id (int): id листа
            participant_list (list): текущий список участников

        Returns:
            list of dict: статус отправки позиций пользователя к нему - стоит ли в очереди, отправлено ли
        """
        
        list_title = self.getSheetListName(sheet_id = list_id)

        ranges = f'{list_title}!A{self.current_list.endRow +1 }:B{self.current_list.endRow + 3 + len(participantList)}'

        rowInfo = self.getSheetListPropertiesById(listId=list_id, includeGridData=True, ranges=[ranges])

        return self.current_list.checkDeliveryToParticipant(rowInfo = rowInfo['data'][0]['rowData'],
                                                            participantList = participantList)