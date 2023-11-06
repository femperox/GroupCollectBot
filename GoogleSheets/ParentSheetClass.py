from pprint import pprint
import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import os
import GoogleSheets.API.Cells_Editor as ce
import json

class ParentSheetClass:

    def __init__(self):
        # Service-объект, для работы с Google-таблицами
        CREDENTIALS_FILE = os.getcwd()+ '/GoogleSheets/creds.json'  # имя файла с закрытым ключом
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())
        self.__service = discovery.build('sheets', 'v4', http=httpAuth)


    def get_spreadsheet_id(self, sp_name):
        """Получить id нужного документа

        Args:
            sp_name (str): имя документа

        Returns:
            str: id нужного документа
        """

        path = os.getcwd()+'/GoogleSheets/sheet_ids.json'
        tmp_dict = json.load(open(path, encoding='utf-8'))
        
        return tmp_dict[sp_name]
    
    def get_sheets(self):
        """Получить информацию о листах документа

        Returns:
            dict: информация о листах документа
        """
        
        infos = self.__service.spreadsheets().get(spreadsheetId=self.__spreadsheet_id).execute()['sheets']
        sheetInfo = {}
        for info in infos:
            sheetInfo[info['properties']['sheetId']] = info['properties']['title']
        
        return sheetInfo