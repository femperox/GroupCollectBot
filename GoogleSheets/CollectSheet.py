from pprint import pprint
import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import GoogleSheets.API.Cells_Editor as ce
from GoogleSheets.API.Styles.Borders import Borders as b
from GoogleSheets.API.Styles.Colors import Colors as c
import os
import json

class CollectSheet:

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

        self.__spreadsheet_id = tmp_dict["collectList"]


    def getSheetListProperties(self, includeGridData = False):
        '''

        :return: Возвращает информацию о листах
        '''

        spId = 1403720531
        sheetName = self.getSheets()[spId]

        range = f"'{sheetName}'!B:E"

        collectList = self.__service.spreadsheets().values().get(spreadsheetId = self.__spreadsheet_id, range=range).execute()['values'][1:]

        for collect in collectList:
            collect[0] = collect[0].split('@')[-1] if collect[0].find('@')>=0 else collect[0].split('/')[-1]
            collect[1] = collect[1].split('@')[-1] if collect[1].find('@')>=0 else collect[1].split('/')[-1]

        return collectList
    
    
    def getSheets(self):
        
        infos = self.__service.spreadsheets().get(spreadsheetId=self.__spreadsheet_id).execute()['sheets']
        sheetInfo = {}
        for info in infos:
            sheetInfo[info['properties']['sheetId']] = info['properties']['title']
        
        return sheetInfo

    def updateURLS(self, urlList):
        vk_preffix = "https://vk.com/"

        spId = 1403720531
        sheetTitle = self.getSheets()[spId]

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []

        row = 2
        for url in urlList:

            ran = f"'{sheetTitle}'!B{row}"
            info = f"{vk_preffix}id{url[0][0]}"
            data.append(ce.insertValue(spId, ran, info))

            ran = ran.replace('!B', '!C')
            info = f"{vk_preffix}club{url[1][0]}"
            data.append(ce.insertValue(spId, ran, info))

            row += 1

        body["data"] = data

        self.__service.spreadsheets().values().batchUpdate(spreadsheetId=self.__spreadsheet_id,
                                                           body=body).execute()
        
    def createCollectView(self, collectList):

        spId = 1928854381
        sheetTitle = self.getSheets()[spId]

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []
        request = []
        request_bold = []
        
        self.__service.spreadsheets().values().clear(spreadsheetId=self.__spreadsheet_id,
                                                     range = f"'{sheetTitle}'!A2:D").execute()
        
        rowHeightRange = {"start":0, "end": 1000}
        
        request.append(ce.unmergeCells(spId, "A2:D1000"))
        request.append(ce.setCellBorder(spId, "A2:D1000"))
        request.append(ce.repeatCells(spId, "A2:D1000", color= c.white))
        request.append(ce.setRowHeight(spId, rowHeightRange, height=35))


        cellColorFlag = True
        
        row = 2
        sortedCollectList = [[collectList[key]['group_name'], key] for key in collectList.keys()]
        sortedCollectList.sort(key = lambda x:x[0])
        sortedCollectList = [x[1] for x in sortedCollectList]

        pprint(list(collectList.keys()))
        pprint(sortedCollectList)

        for key in sortedCollectList:
                       
            start_row = row 

            ran = f"'{sheetTitle}'!A{row}"
 
            # Ссылка на сообщество
            collect_url = f'''=HYPERLINK("https://vk.com/club{key}"; "{collectList[key]['group_name']}")'''
            data.append(ce.insertValue(spId, ran, collect_url))

            # ник на самурае
            ran = ran.replace("!A", "!B")
            data.append(ce.insertValue(spId, ran, collectList[key]['samurai']))
            
            # инфо про админов
            for admin in collectList[key]['admins']:
               
                ran = f"'{sheetTitle}'!C{row}"
                admin_url = f'''=HYPERLINK("https://vk.com/id{admin[0]}"; "{admin[1]}")''' 
                data.append(ce.insertValue(spId, ran, admin_url))
                ran = ran.replace("!C", "!D")
                data.append(ce.insertValue(spId, ran, admin[2]))
                row +=1
            
            #обединение ячеек
            if start_row < row - 1:
                request.append(ce.mergeCells(spId, f"A{start_row}:A{row-1}"))
                request.append(ce.mergeCells(spId, f"B{start_row}:B{row-1}"))

            # рамки ячеек
            request.append(ce.setCellBorder(spId, f"A{start_row}:D{row}", bstyleList=b.plain_black))
            request_bold.append(ce.setCellBorder(spId, f"A{start_row}:D{row}", all_same=False, bstyleList=[b.medium_black, b.plain_black, b.plain_black, b.plain_black, b.plain_black, b.plain_black]))
            
            if cellColorFlag:
                request.append(ce.repeatCells(spId, f"A{start_row}:D{row-1}", color= c.white_blue))
            
            cellColorFlag = not cellColorFlag    
            
        
        body["data"] = data

        request.extend(request_bold)
        
        self.__service.spreadsheets().batchUpdate(spreadsheetId=self.__spreadsheet_id,
                                                  body={"requests": request}).execute()
        
        self.__service.spreadsheets().values().batchUpdate(spreadsheetId=self.__spreadsheet_id,
                                                           body=body).execute()






