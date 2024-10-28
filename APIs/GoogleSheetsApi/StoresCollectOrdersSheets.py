
from APIs.GoogleSheetsApi.ParentSheetClass import ParentSheetClass
import re
import APIs.GoogleSheetsApi.API.Cells_Editor as ce
from APIs.GoogleSheetsApi.API.Styles.Borders import Borders as b
from APIs.GoogleSheetsApi.API.Styles.Colors import Colors as c
from APIs.GoogleSheetsApi.Spreadsheets.StoresCollectOrdersList import StoresCollectOrdersList
from confings.Consts import OrderTypes
from APIs.utils import concatList
from pprint import pprint
from datetime import datetime
import locale

class StoresCollectOrdersSheets(ParentSheetClass):
    
    def __init__(self):

        super().__init__()
        self.setSpreadsheetId("storesCollectList")
        self.current_list = StoresCollectOrdersList()

    def createNewStoresCollect(self, title, topic_url, participant_count, order_type = OrderTypes.ami):

        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        list_title = title + ' ' + datetime.strftime(datetime.now(), '%b %Y')
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

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

        list_title = self.getSheetListPropertiesById(listId=list_id)['properties']['title']

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
