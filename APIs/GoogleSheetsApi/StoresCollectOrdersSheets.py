
from APIs.GoogleSheetsApi.ParentSheetClass import ParentSheetClass
import re
import APIs.GoogleSheetsApi.API.Cells_Editor as ce
from APIs.GoogleSheetsApi.API.Styles.Borders import Borders as b
from APIs.GoogleSheetsApi.API.Styles.Colors import Colors as c
from APIs.GoogleSheetsApi.Spreadsheets.StoresCollectOrdersList import StoresCollectOrdersList
from confings.Consts import OrderTypes
from APIs.utils import concatList
from pprint import pprint

class StoresCollectOrdersSheets(ParentSheetClass):
    
    def __init__(self):

        super().__init__()
        self.setSpreadsheetId("testList")
        self.current_list = StoresCollectOrdersList()

    def createNewStoresCollect(self, title, topic_url, participant_count, order_type = OrderTypes.ami):

        list_id = self.createSheetList(title = title)
        
        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                body={"requests": self.current_list.prepareTable(list_id=list_id, 
                                                                                                 participant_count = participant_count,
                                                                                                 order_type = order_type)}).execute()
        
        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                    body = self.current_list.prepareTableValues(list_id = list_id,
                                                                                                list_title = title,
                                                                                                topic_url = topic_url,
                                                                                                order_type = order_type)).execute()
        return list_id

    def updateStoresCollect(self, list_id, participant_list, participant_count_old):

        list_title = self.getSheetListPropertiesById(listId=list_id)['properties']['title']
        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                body={"requests": self.current_list.updateTable(list_id = list_id, 
                                                                                                participant_count_new = len(participant_list),
                                                                                                participant_count_old = participant_count_old)}).execute()

        self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                         body=self.current_list.updateTableValues(list_id = list_id,
                                                                                                  list_title = list_title,
                                                                                                  participant_list = participant_list)).execute()
