import APIs.GoogleSheetsApi.API.Cells_Editor as ce
from APIs.GoogleSheetsApi.API.Styles.Borders import Borders as b
from APIs.GoogleSheetsApi.API.Styles.Colors import Colors as c
from APIs.GoogleSheetsApi.API.Constants import ConditionType
from pprint import pprint

class StoresCollectOrdersList:

    def prepareTable(self, list_id):
        
        request = []
        startRow = 1
        endRow = 14

        # объдинение ячеек
        request.append(ce.mergeCells(list_id, f"A{startRow+1}:I{endRow-1}"))

        # стили ячеек
        request.append(ce.repeatCells(list_id, f"A{startRow}:B{startRow}", c.light_purple))
        request.append(ce.repeatCells(list_id, f"A{endRow}:H{endRow}", c.light_purple))
        request.append(ce.repeatCells(list_id, f"I{endRow}:I{endRow}", c.turquoise))

        # границы ячеек
        request.append(ce.setCellBorder(list_id, f"A{startRow}:B{startRow}", bstyleList=b.plain_black))
        request.append(ce.setCellBorder(list_id, f"A{startRow+1}:I{endRow}", bstyleList=b.plain_black))


        return request