import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import APIs.GoogleSheetsApi.API.Cells_Editor as ce
import json 
from confings.Consts import CREDENTIALS_FILE, SHEETS_ID_FILE
from pprint import pprint
from traceback import print_exc

class ParentSheetClass:

    def __init__(self):
        # Service-объект, для работы с Google-таблицами
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())
        self.service = discovery.build('sheets', 'v4', http=httpAuth)
        

    def renameSheetList(self, sheet_id, title):
        """Изменить имя листа

        Args:
            sheet_id (int): id листа
            title (string): новое название
        """

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(), body={'requests': ce.updateSheetProperties(spId = sheet_id, newTitle = title)}).execute()

    def changeSheetListIndex(self, sheet_id, new_index):
        """Изменить расположение листа в документе

        Args:
            sheet_id (int): id листа
            new_index (int): новый индекс
        """

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(), body={'requests': ce.updateSheetProperties(spId = sheet_id, newIndex = new_index)}).execute()

    def copySheetListTo(self, sheet_id, new_spreadsheet_id):
        """Скопировать лист в другой документ

        Args:
            sheet_id (int): id листа
            new_spreadsheet_id (string): id документа
        """
        
        return self.service.spreadsheets().sheets().copyTo(spreadsheetId=self.getSpreadsheetId(), sheetId = sheet_id, body = {"destination_spreadsheet_id": new_spreadsheet_id}).execute()

    def deleteSheetList(self, sheet_id):
        """Удалить лист из документа

        Args:
            sheet_id (int): id листа
        """

        self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                body={"requests": ce.deleteSheet(sheet_id = sheet_id)}).execute()        

    def getSheetListName(self, sheet_id):
        """Получить название листа

        Args:
            sheet_id (int): id листа

        Returns:
            string: название листа
        """

        return self.getSheetListPropertiesById(listId = sheet_id)['properties']['title']

    def createSheetList(self, title):
        """создать лист в таблице

        Args:
            title (string): название листа

        Returns:
            int: id листа
        """

        try:
            result = self.service.spreadsheets().batchUpdate(spreadsheetId=self.getSpreadsheetId(),
                                                  body={"requests": ce.addSheet(title = title)}).execute()
            return result['replies'][0]['addSheet']['properties']['sheetId']
        
        except Exception as e:
            pprint(e)
            print_exc()
            return -1

    def setSpreadsheetId(self, sp_name):

        tmp_dict = json.load(open(SHEETS_ID_FILE, encoding='utf-8'))

        self.__spreadsheet_id = tmp_dict[sp_name]

    def getSpreadsheetId(self):
    
        return self.__spreadsheet_id
    
    def get_sheets(self):
        """Получить информацию о листах документа

        Returns:
            dict: информация о листах документа
        """
        
        infos = self.service.spreadsheets().get(spreadsheetId = self.__spreadsheet_id ).execute()['sheets']
        sheetInfo = {}
        for info in infos:
            sheetInfo[info['properties']['sheetId']] = info['properties']['title']
        
        return sheetInfo
    
    def getJsonNamedRange(self, namedRange, typeCalling = 0, valueRenderOption ="FORMULA"):
        '''
        Запрос на поиск именного запроса по его имени

        :param namedRange: имя Именованного диапозона
        :param typeCalling: тип вызова. 0 - получить только диапозон, 1 - получить полную инфу о диапозоне
        :param valueRenderOption: в какой форме получать содержимое ячеек
        :return: возвращает часть реквеста, а именно диапозон
        '''
        try:
           result = self.service.spreadsheets().values().get(spreadsheetId= self.__spreadsheet_id, range=namedRange, valueRenderOption = valueRenderOption).execute()
        except Exception as e:
           print(e)
           result = {"range": -1}
        if typeCalling == 0 : return result["range"]
        else: return result

    def getSheetListProperties(self, includeGridData = False, ranges = []):
        '''

        :return: Возвращает информацию о листах
        '''

        spreadsheet = self.service.spreadsheets().get(spreadsheetId = self.__spreadsheet_id, 
                                                      includeGridData = includeGridData,
                                                      ranges = ranges).execute()
        return spreadsheet.get('sheets')
    
    def getSheetListPropertiesById(self, listId, includeGridData = False, ranges = []):
        """Получить информацию о конкретном листе

        Args:
            listId (int): id листа
            includeGridData (bool, optional): флаг GridData. Defaults to False.

        Returns:
            dict: информация о конкретном листе
        """

        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId = self.__spreadsheet_id, 
                                                          includeGridData = includeGridData,
                                                          ranges = ranges).execute()
        
            properties = spreadsheet.get('sheets')
            for property in properties:
                if property['properties']['sheetId'] == listId:
                    return property
            return {}
        except Exception as e:
            pprint(e)
            return {}
    
    def getRowData(self, namedRange, typeCalling = 0, cell_point = 0):
        '''
        Подробная информация о строках заданного диапозона

        :param namedRange:
        :param typeCalling: тип вызова. 0 - инфа без участников. 1 - инфа об участниках
        :param cell_point: регулировщик сдвига по ячейкам.
        :return:
        '''

        sheetTitle, range_ = self.getJsonNamedRange(namedRange).split('!')

        start, end = range_.split(':')

        if typeCalling == 0:
            start = chr(ord(start[0]) + 3) + str(int(start[1:]) + 14)
            end = chr(ord(end[0]) - 2 - cell_point) + str(int(end[1:]) - 1)
        else:
            end = chr(ord(start[0]) + 1) + str(int(end[1:]) - 1)
            start = chr(ord(start[0]) + 1) + str(int(start[1:]) + 14)

        range_ = '{0}!{1}:{2}'.format(sheetTitle, start, end)

        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.__spreadsheet_id, ranges=range_,
                                                        includeGridData=True).execute()

        return spreadsheet["sheets"][0]['data'][0]["rowData"]