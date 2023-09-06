from pprint import pprint
import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import os
import GoogleSheets.API.Cells_Editor as ce
import json

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
        path = os.getcwd()+'/GoogleSheets/sheet_ids.json'
        tmp_dict = json.load(open(path, encoding='utf-8'))
        self.__spreadsheet_id = tmp_dict["tagList"]

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
    
    #TODO: Класс родитель
    def getSheets(self):
        
        infos = self.__service.spreadsheets().get(spreadsheetId=self.__spreadsheet_id).execute()['sheets']
        sheetInfo = {}
        for info in infos:
            sheetInfo[info['properties']['sheetId']] = info['properties']['title']
        
        return sheetInfo
    
    def updateURLS(self, urlList):
        vk_preffix = "https://vk.com/"

        spId = 405719641
        sheetTitle = self.getSheets()[spId]

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []

        row = 2
        for url in urlList:

            ran = f"'{sheetTitle}'!B{row}"
            info = f"{vk_preffix}id{url[0]}"
            data.append(ce.insertValue(spId, ran, info))

            row += 1

        body["data"] = data

        self.__service.spreadsheets().values().batchUpdate(spreadsheetId=self.__spreadsheet_id,
                                                           body=body).execute()


