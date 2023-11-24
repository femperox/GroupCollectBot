import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import json
from confings.Consts import CREDENTIALS_FILE, SHEETS_ID_FILE

class ParentSheetClass:

    def __init__(self):
        # Service-объект, для работы с Google-таблицами
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())
        self.service = discovery.build('sheets', 'v4', http=httpAuth)
        

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
        except :
           result = {"range": -1}

        if typeCalling == 0 : return result["range"]
        else: return result

    def getSheetListProperties(self, includeGridData = False):
        '''

        :return: Возвращает информацию о листах
        '''

        spreadsheet = self.service.spreadsheets().get(spreadsheetId = self.__spreadsheet_id, includeGridData = includeGridData).execute()
        return spreadsheet.get('sheets')
    
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