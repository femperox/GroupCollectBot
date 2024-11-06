from APIs.GoogleSheetsApi.API.Styles.Borders import Borders as b
from APIs.GoogleSheetsApi.API.Styles.Colors import Colors as c

def toRangeType(spId, range):
    '''
    Конвертирует диапозон ячеек в словарь

    :param spId: айди листа в таблице
    :param range: диапозон ячеек в формате "В1:С45" - пример
    :return: возвращает словарь для json запроса
    '''

    rangeType = {}
    rangeType["sheetId"] = spId

    try: # Формат *#:*#
      startCell, endCell = range.split(":")[0:2]

      rangeType["startRowIndex"] = int(startCell[1:]) -1
      rangeType["startColumnIndex"] = ord(startCell[0]) - ord('A')

      rangeType["endRowIndex"] = endCell[1:]
      rangeType["endColumnIndex"] = ord(endCell[0]) - ord('A') + 1
    except: # Формат *#
      rangeType["rowIndex"] = int(range[1:]) -1
      rangeType["columnIndex"] = ord(range[0]) - ord('A')

    return rangeType


def toUserEnteredFormat(color, hali = 'CENTER', vali = 'MIDDLE', textFormat = 'True'):
    '''
    составляет словарь стиля ячейки

    :param color: цвет
    :param hali: вертикальное выравнивание
    :param vali: горизонтальное выравнивание
    :param textFormat: формат текста
    :return: возвращает словарь для json запроса
    '''
    userEnteredFormat = {}
    #userEnteredFormat["numberFormat"] = { "type": "TEXT" }
    userEnteredFormat['horizontalAlignment'] = hali
    userEnteredFormat['verticalAlignment'] = vali
    userEnteredFormat['textFormat'] = {'bold': textFormat}
    userEnteredFormat["backgroundColor"] = color
    userEnteredFormat["wrapStrategy"] = "WRAP"

    return userEnteredFormat


def addConditionalFormatRuleColorChange(spId, range, ruleType, ruleValue, ruleColor):
  """Составить запрос для условного форматирования - смена цвета ячейки в зависимости от ее значения

  Args:
      spId (int): id листа в документе таблицы
      range (string): диапозон ячеек в формате "В1:С45" - пример
      ruleType (ConditionType): тип правила условного форматирования
      ruleValue (string): значения для правила условного форматирования
      ruleColor (Colors): цвет, в который ячейка будет окрашиваться

  Returns:
      dict: словарь для json запроса
  """
    
  request = {
      "addConditionalFormatRule":
      {
          "rule": 
          {
              "ranges": [toRangeType(spId, range)],
              "booleanRule":
              {
                  "condition": 
                  {
                      "type": ruleType,
                      "values": [{ "userEnteredValue": ruleValue}]
                  },  
                  "format":
                  {
                        "backgroundColor": ruleColor
                  }
              }

          }
      }
  }

  return request




def mergeCells(spId, range):
    '''
    подготовка json запроса для объединения ячеек таблицы по заданным параметрам

    :param spId: айди листа в таблице
    :param range: диапозон ячеек в формате "В1:С45" - пример
    :return: возвращает json запрос
    '''
    request = {"mergeCells":
                { "range" : toRangeType(spId, range),
                  "mergeType": "MERGE_ALL"
                }
              }
    return request


def unmergeCells(spId, range):
    '''
    подготовка json запроса для разъединения ячеек таблицы по заданным параметрам

    :param spId: айди листа в таблице
    :param range: диапозон ячеек в формате "В1:С45" - пример
    :return: возвращает json запрос
    '''
    request = {"unmergeCells": { "range": toRangeType(spId, range) } }
    return request


def setCellBorder(spId, range, all_same = True, only_outer = False, bstyleList = b.no_border):
    '''
    подготовка json запроса для обрамления диапозона ячеек границами с определёнными стилями

    :param spId: айди листа в таблице
    :param range: диапозон ячеек в формате "В1:С45" - пример
    :param all_same: Применять ли ко всем сторонам ячейки одинаковый стиль границ. По умолчанию - да
    :param bstyleList: Список стилей границ. По умолчанию - "без граниу"
    :return: возвращает json запрос
    '''

    if not isinstance(bstyleList, list): bstyleList = [bstyleList]

    if len(bstyleList) < 6:
        bstyleList = bstyleList + [b.no_border]*(6-len(bstyleList))

    if all_same:
        bstyleList = [bstyleList[0]]*6

    if only_outer:
        bstyleList[4] = b.no_border
        bstyleList[5] = b.no_border

    request = {"updateBorders":
                { "range" : toRangeType(spId, range),
                  "top": bstyleList[0],
                  "bottom": bstyleList[1],
                  "left": bstyleList[2],
                  "right": bstyleList[3],
                  "innerHorizontal": bstyleList[4],
                  "innerVertical": bstyleList[5]
                }
              }
    return request


def repeatCells(spId, range, color, hali = "CENTER", textFormat = 'True'):
    '''
    подготовка json запроса для оформления диапозона ячеек определённым стилем

    :param spId: айди листа в таблице
    :param range: диапозон ячеек в формате "В1:С45" - пример
    :param color: цвет ячейки
    :return: возвращает json запрос
    '''

    request = { "repeatCell":
                { "range": toRangeType(spId, range),
                  "cell": { "userEnteredFormat": toUserEnteredFormat(color, hali = hali, textFormat = textFormat) },
                  "fields": "userEnteredFormat"
                }

    }

    return request


def deleteRange(spId, range):
    '''
    Удаление заданного диапозона ячеек из таблиуы

    :param spId: айди листа в таблице
    :param range: диапозон ячеек в формате "В1:С45" - пример
    :return: возвращает json запрос
    '''

    request = { "deleteRange":
                { "range" : toRangeType(spId, range),
                  "shiftDimension" : "ROWS"
                }
              }

    return request


def CutPasteRange(spId, range, newRange, newSpId = None):
    '''
    Вставка диапозона ячеек из одного места в другое

    :param spId: айди листа в таблице
    :param range: диапозон ячеек в формате "В1:С45" - пример
    :param newRange: новый диапозон ячеек
    :param newSpId: новый айди листа в таблице
    :return: возвращает json запрос
    '''

    if newSpId is None:
        newSpId = spId

    request = { "cutPaste":
                { "source": toRangeType(spId, range),
                  "destination": toRangeType(newSpId, newRange),
                  "pasteType": "PASTE_NORMAL"
                }
              }

    return request

def copyPasteRange(spId, range, newRange, newSpId = None):
  """Скопировать вставить диапозон

  Args:
      spId (int): id листа откуда
      range (string): диапозон откуда
      newRange (string): диапозон куда
      newSpId (int, optional): id листа куда. Defaults to None.

  Returns:
      _type_: _description_
  """
  if newSpId is None:
      newSpId = spId

  request = { "copyPaste":
              { "source": toRangeType(spId, range),
                "destination": toRangeType(newSpId, newRange),
                "pasteType": "PASTE_NORMAL"
              }
            }

  return request


def addNamedRange(spId, range, name):
    '''
    Добавляет именнованный диапозон по заданным параметрам

    :param spId: айди листа в таблице
    :param range: диапозон ячеек в формате "В1:С45" - пример
    :param name: имя диапозона
    :return: возвращает json запрос
    '''

    request = {"addNamedRange":
                   {  "namedRange":
                      {  "namedRangeId": name,
                         "name": name,
                         "range": toRangeType(spId,range)
                      }
                   }
               }
    return request


def deleteNamedRange(name):
    '''
    Удаляет именованный диапозон по заданному имени

    :param name: имя диапозона
    :return: возвращает json запрос
    '''


    request = {"deleteNamedRange":
                   {"namedRangeId": name}
              }

    return request


def deleteSheet(sheet_id):
    """Удаляет лист из документа

    Args:
        sheet_id (int): id листа

    Returns:
        dict: json запрос
    """

    request = {
      "deleteSheet": {
        "sheetId": sheet_id
      }
    }

    return request


def insertValue(spId, range, text ="", majorDime = "ROWS"):
    '''
    подготовка json запроса для заполнения ячеек заданным текстом

    :param spId: айди листа в таблице
    :param range: диапозон ячеек в формате "НазваниеЛиста!В1:С45" - пример
    :param text: текст ячейки
    :param majorDime: формат заполнения ячеек
    :return: возвращает json запрос
    '''

    data = {}

    data["range"] = range
    data["majorDimension"] = majorDime
    data["values"] = [[text]]

    return data

def updateSheetProperties(spId, newTitle = '', addingRows = 0, newIndex = 0):

    if addingRows:
        fields = 'gridProperties'
    elif newTitle:
        fields = 'title'
    elif newIndex:
        fields = 'index'
    request = {  "updateSheetProperties": {"properties":
                                                        { "sheetId": spId,
                                                          "title": newTitle,
                                                          "index": newIndex,
                                                          "gridProperties": {"rowCount" : addingRows,
                                                                             'columnCount': 24
                                                                             }
                                                        },
                                                    "fields" : fields
                                                  }
    }

    return request


def insertRange(spId, range):

    request = { "insertRange": { "range": toRangeType(spId, range),
                                 "shiftDimension" : "ROWS"
                               }

    }

    return request
  
def setRowHeight(spId, range, height):
  
  request = { "updateDimensionProperties": 
              {
                  "range": 
                  {
                    "sheetId": spId,
                    "dimension": "ROWS",
                    "startIndex": range['start'],
                    "endIndex": range['end']
                  },
                  "properties": 
                  {
                    "pixelSize": height
                  },
                  "fields": "pixelSize"
              }
            }
  
  return request

def addSheet(title, index = 0):
  """подготовка json запроса для добавлния листа 

  Args:
      title (string): название листа

  Returns:
      dict: json запрос
  """

  request = { "addSheet": 
              {"properties": 
                { "title": title,
                  "tabColor": c.white,
                  "index": index
                }
              }
            }

  return request