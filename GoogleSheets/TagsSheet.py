from pprint import pprint
import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import os
import GoogleSheets.API.Cells_Editor as ce
import json
from GoogleSheets.ParentSheetClass import ParentSheetClass

class TagsSheet(ParentSheetClass):

    def __init__(self):

        self.__spreadsheet_id = self.get_spreadsheet_id("tagList")

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
    
    
    def updateURLS(self, urlList):
        """Приведение ссылок в id-вид с начала листа

        Args:
            urlList (list): список ссылок
        """

        vk_preffix = "https://vk.com/"

        spId = 405719641
        sheetTitle = self.get_sheets()[spId]

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


