import APIs.GoogleSheetsApi.API.Cells_Editor as ce
from APIs.GoogleSheetsApi.ParentSheetClass import ParentSheetClass

class TagsSheet(ParentSheetClass):

    def __init__(self):

        super().__init__()
        self.setSpreadsheetId("tagList")

        self.lastFree = 1


    def getSheetListProperties(self):
        '''

        :return: Возвращает информацию о листах
        '''

        sheetName = self.service.spreadsheets().get(spreadsheetId= self.getSpreadsheetId()).execute()['sheets'][0]['properties']['title']

        range = f"'{sheetName}'!B{self.lastFree}:C"

        fandomList = self.service.spreadsheets().values().get(spreadsheetId = self.getSpreadsheetId(), range=range).execute()['values'][1:]

        self.lastFree = len(fandomList)+1

        for usr in fandomList:
            try:
                usr[0]= usr[0].split('@')[-1] if usr[0].find('@') >= 0 else usr[0].split('/')[-1]
                usr[1] = usr[1].replace(' ', '').split(',')
            except:
                continue

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

        self.service.spreadsheets().values().batchUpdate(spreadsheetId = self.getSpreadsheetId(),
                                                           body=body).execute()


