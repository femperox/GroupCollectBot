import GoogleSheets.API.Cells_Editor as ce
from GoogleSheets.API.Styles.Borders import Borders as b
from GoogleSheets.API.Styles.Colors import Colors as c
from GoogleSheets.ParentSheetClass import ParentSheetClass
from pprint import pprint

class CollectSheet(ParentSheetClass):

    def __init__(self):

        super().__init__()
        self.setSpreadsheetId("collectList")

    def getSheetListProperties(self, includeGridData = False):
        """Вообще не помню чё длает)

        Args:
            includeGridData (bool, optional): _description_. Defaults to False.

        Returns:
            _type_: _description_
        """

        spId = 1403720531
        sheetName = self.get_sheets()[spId]

        range = f"'{sheetName}'!B:E"
        
        collectList = self.service.spreadsheets().values().get(spreadsheetId = self.getSpreadsheetId(), range=range).execute()['values'][1:]

        newCollectList = []

        for collect in collectList:
            if collect:
                collect_first = collect[0].split('@')[-1] if collect[0].find('@')>=0 else collect[0].split('/')[-1]
                collect_second = collect[1].split('@')[-1] if collect[1].find('@')>=0 else collect[1].split('/')[-1]
                newCollectList.append([collect_first, collect_second, collect[2], collect[3]])

        return newCollectList
    
    def updateURLS(self, urlList):
        """Приведение ссылок в id-вид с начала листа

        Args:
            urlList (list): список ссылок
        """

        vk_preffix = "https://vk.com/"

        spId = 1403720531
        sheetTitle = self.get_sheets()[spId]

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []

        row = 2
        for url in urlList:

            if url:
                ran = f"'{sheetTitle}'!B{row}"
                info = f"{vk_preffix}id{url[0][0]}"
                data.append(ce.insertValue(spId, ran, info))

                ran = ran.replace('!B', '!C')
                info = f"{vk_preffix}club{url[1][0]}"
                data.append(ce.insertValue(spId, ran, info))

                ran = ran.replace('!C', '!D')
                info = url[2]
                data.append(ce.insertValue(spId, ran, info))

                ran = ran.replace('!D', '!E')
                info = url[3]
                data.append(ce.insertValue(spId, ran, info))

            row += 1

        body["data"] = data

        self.service.spreadsheets().values().clear(spreadsheetId = self.getSpreadsheetId(),
                                                     range = f"'{sheetTitle}'!A2:E").execute()        

        self.service.spreadsheets().values().batchUpdate(spreadsheetId = self.getSpreadsheetId(),
                                                           body=body).execute()
        
    def createCollectView(self, collectList):
        """ Генерация таблицы коллектов

        Args:
            collectList (list): список коллектов
        """

        spId = 1928854381
        sheetTitle = self.get_sheets()[spId]

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []
        request = []
        request_bold = []
        
        self.service.spreadsheets().values().clear(spreadsheetId = self.getSpreadsheetId(),
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
        
        self.service.spreadsheets().batchUpdate(spreadsheetId= self.getSpreadsheetId(),
                                                  body={"requests": request}).execute()
        
        self.service.spreadsheets().values().batchUpdate(spreadsheetId= self.getSpreadsheetId(),
                                                           body=body).execute()






