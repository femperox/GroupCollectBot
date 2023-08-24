from pprint import pprint
import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import os

class TagsSheet:

    def __init__(self):
        # Service-объект, для работы с Google-таблицами
        CREDENTIALS_FILE = os.getcwd()+ '/GoogleSheets/creds.json'  # имя файла с закрытым ключом
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())
        self.__service = discovery.build('sheets', 'v4', http=httpAuth)

        # id гугл таблицы
        self.__spreadsheet_id = '1KpRHGOuirl2oVEJIurFRjX0iqeMIW7jJo2bP9bGJIjU'

        self.lastFree = 1


    def getSheetListProperties(self):
        '''

        :return: Возвращает информацию о листах
        '''

        sheetName = self.__service.spreadsheets().get(spreadsheetId=self.__spreadsheet_id).execute()['sheets'][0]['properties']['title']

        range = f"'{sheetName}'!B{self.lastFree}:C"

        fandomList = self.__service.spreadsheets().values().get(spreadsheetId = self.__spreadsheet_id, range=range).execute()['values'][1:]

        self.lastFree = len(fandomList)+1

        for usr in fandomList:
            usr[0]= usr[0].split('@')[-1] if usr[0].find('@') >= 0 else usr[0].split('/')[-1]
            usr[1] = usr[1].replace(' ', '').split(',')


        return fandomList


