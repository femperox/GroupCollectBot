import APIs.GoogleSheetsApi.API.Cells_Editor as ce
from APIs.GoogleSheetsApi.API.Styles.Borders import Borders as b
from APIs.GoogleSheetsApi.API.Styles.Colors import Colors as c
from APIs.GoogleSheetsApi.ParentSheetClass import ParentSheetClass
from pprint import pprint



class CollectSheet(ParentSheetClass):
    class SpreadsheetKeyClass:
        rawShopsCollectsList = "rawShopsCollectsList"
        publicShopsCollectsList = "publicShopsCollectsList"

    class SheetIdClass:
        rawShopsSheetId = "rawShopsSheetId"
        rawCollectsSheetId = "rawCollectsSheetId"
        publicShopsSheetId = "publicShopsSheetId"
        publicCollectsSheetId = "publicCollectsSheetId"

    def __init__(self, spreadsheetKey: SpreadsheetKeyClass = SpreadsheetKeyClass.rawShopsCollectsList):
        super().__init__()
        self.setSpreadsheetId(spreadsheetKey)

    def getSheetListProperties(self, spId, startRow = 2):
        """Получить содержание строк

        Args:
            spId (int): id листа
            startRow (int, optional): номер строки начала выгрузки. Defaults to 2.

        Returns:
            dict: словарь вида {'collectList': list of dict, 'nextSeenRow': int}
        """
        sheetName = self.get_sheets()[spId]

        range = f"'{sheetName}'!B{startRow}:H"
        newCollectList = []
        collectList = self.service.spreadsheets().values().get(spreadsheetId = self.getSpreadsheetId(), range=range).execute()

        if 'values' in collectList.keys():
            collectList = collectList['values']

            for collect in collectList:
                if collect:
                    admin_id = collect[0].split('@')[-1] if collect[0].find('@')>=0 else collect[0].split('/')[-1]
                    group_id = collect[1].split('@')[-1] if collect[1].find('@')>=0 else collect[1].split('/')[-1]
                    newCollectList.append({'admin_id':admin_id, 'group_id':group_id, 'admin_role': collect[2], 
                                        'city': collect[3] if len(collect) >= 4 else '',
                                        'countries': collect[4] if len(collect) >= 5 else '',
                                        'shops': collect[5] if len(collect) >= 6 else '',
                                        'fandoms': collect[6] if len(collect) >= 7 else '',
                                        }.copy())
        
        nextSeenRow = startRow + len(collectList)
        return {'collectList':newCollectList, 'nextSeenRow': nextSeenRow}
    
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

            row += 1

        body["data"] = data

        self.service.spreadsheets().values().clear(spreadsheetId = self.getSpreadsheetId(),
                                                     range = f"'{sheetTitle}'!A2:E").execute()        

        self.service.spreadsheets().values().batchUpdate(spreadsheetId = self.getSpreadsheetId(),
                                                           body=body).execute()
        
    def createCollectView(self, collectList, spId):
        """ Генерация таблицы коллектов

        Args:
            collectList (list): список коллектов
        """

        sheetTitle = self.get_sheets()[spId]

        body = {}
        body["valueInputOption"] = "USER_ENTERED"

        data = []
        request = []
        request_bold = []
        
        self.service.spreadsheets().values().clear(spreadsheetId = self.getSpreadsheetId(),
                                                     range = f"'{sheetTitle}'!A2:E").execute()
        
        rowHeightRange = {"start":0, "end": 1000}
        
        request.append(ce.unmergeCells(spId, "A2:E1000"))
        request.append(ce.setCellBorder(spId, "A2:E1000"))
        request.append(ce.repeatCells(spId, "A2:E1000", color= c.white))
        request.append(ce.setRowHeight(spId, rowHeightRange, height=65))


        cellColorFlag = True
        
        row = 2
        
        for collect in collectList:
                       
            start_row = row 

            ran = f"'{sheetTitle}'!A{row}"

            # Картинка
            collect_picture_url = f'''=IMAGE("{collect['pictureUrl']}")'''
            data.append(ce.insertValue(spId, ran, collect_picture_url))
 
            # Ссылка на сообщество
            collect_url = f'''=HYPERLINK("https://vk.com/club{collect['groupId']}"; "{collect['groupName']}")'''
            ran = ran.replace("!A", "!B")
            data.append(ce.insertValue(spId, ran, collect_url))

            # доп инфо о коллекте/шопе
            additional_text = '✧ ' + '\n✧ '.join([collect['groupInfo'][key] for key in collect['groupInfo'].keys()])
            ran = ran.replace("!B", "!E")
            data.append(ce.insertValue(spId, ran, additional_text))

            # инфо про админов
            for admin in collect['admins']:
                
                ran = f"'{sheetTitle}'!C{row}"
                admin_url = f'''=HYPERLINK("https://vk.com/id{admin['adminId']}"; "{admin['adminName']}")''' 
                data.append(ce.insertValue(spId, ran, admin_url))
                ran = ran.replace("!C", "!D")
                data.append(ce.insertValue(spId, ran, admin['adminRole']))
                row +=1
            
            #обединение ячеек
            if start_row < row - 1:
                request.append(ce.mergeCells(spId, f"A{start_row}:A{row-1}"))
                request.append(ce.mergeCells(spId, f"B{start_row}:B{row-1}"))
                request.append(ce.mergeCells(spId, f"E{start_row}:E{row-1}"))

            # рамки ячеек
            request.append(ce.setCellBorder(spId, f"A{start_row}:E{row}", bstyleList=b.plain_black))
            request_bold.append(ce.setCellBorder(spId, f"A{start_row}:E{row}", all_same=False, bstyleList=[b.medium_black, b.plain_black , b.plain_black, b.plain_black, b.plain_black, b.plain_black]))
            
            if cellColorFlag:
                request.append(ce.repeatCells(spId, f"A{start_row}:E{row-1}", color= c.white_blue))
            
            cellColorFlag = not cellColorFlag    

        request_bold.append(ce.setCellBorder(spId, f"A1:A{row}", all_same=False, bstyleList=[b.no_border, b.no_border, b.no_border, b.no_border, b.medium_black, b.no_border]))
        request_bold.append(ce.setCellBorder(spId, f"A{row}:E{row}", all_same=False, bstyleList=[b.medium_black, b.no_border, b.no_border, b.no_border, b.no_border, b.no_border]))

        body["data"] = data

        request.extend(request_bold)
        
        self.service.spreadsheets().batchUpdate(spreadsheetId= self.getSpreadsheetId(),
                                                  body={"requests": request}).execute()
        
        self.service.spreadsheets().values().batchUpdate(spreadsheetId= self.getSpreadsheetId(),
                                                           body=body).execute()






