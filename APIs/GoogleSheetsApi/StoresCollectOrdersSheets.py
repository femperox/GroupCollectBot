
from APIs.GoogleSheetsApi.ParentSheetClass import ParentSheetClass
import re
import APIs.GoogleSheetsApi.API.Cells_Editor as ce
from APIs.GoogleSheetsApi.API.Styles.Borders import Borders as b
from APIs.GoogleSheetsApi.API.Styles.Colors import Colors as c
from APIs.GoogleSheetsApi.Spreadsheets.StoresCollectOrdersList import StoresCollectOrdersList
from APIs.utils import concatList
from pprint import pprint

class StoresCollectOrdersSheets(ParentSheetClass):
    
    def __init__(self):

        super().__init__()
        self.setSpreadsheetId("testList")
        self.current_list = StoresCollectOrdersList()

    def createNewStoresCollect(self, title):

        list_id = self.createSheetList(title = title)
        
        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                body={"requests": self.current_list.prepareTable(list_id=list_id)}).execute()
