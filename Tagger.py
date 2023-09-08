from GoogleSheets.TagsSheet import TagsSheet as ts
from GoogleSheets.CollectSheet import CollectSheet as cs
from VkApi.VkInterface import VkApi as vk
from pprint import pprint
from time import sleep
from SQLS.DB_Operations import addTags
from confings.Consts import HOURS_12
import threading

TIME_CHECK_SHEET = HOURS_12
TIME_CHECK_COLLECTS = TIME_CHECK_SHEET*2

def addNewUsers():
    while True:
        list = ts.getSheetListProperties()
        for usr in list:            
            usr[0] = vk.get_id(usr[0])

            for fandom in usr[1]:
                pprint( f'{addTags(usr[0], fandom)} for {usr[0]}')
        
        ts.updateURLS(list)
        sleep(TIME_CHECK_SHEET)

def checkCollects():
    
    while True:
        
        collectList = cs.getSheetListProperties()

        for collect in collectList:
        
            collect[0] = vk.get_name(collect[0]).split('(')
            collect[0][0] = collect[0][0].replace('@id', '')
            collect[0][1] = collect[0][1].replace(')', '')

            collect[1] = vk.get_group_name(collect[1]).split('(')
            collect[1][0] = collect[1][0].replace('@club', '')
            collect[1][1] = collect[1][1].replace(')', '')
        
        cs.updateURLS(collectList)
            
        distinct_collects = set([collect[1][0] for collect in collectList])
        
        new_list = {}
        # сортировка по коллеткам
        for collect in distinct_collects:
            cList = []
            full_list = {}
            for rawCollect in collectList:
                if collect == rawCollect[1][0]:
                    cList.append([rawCollect[0][0], rawCollect[0][1], rawCollect[-2]])
                    full_list["samurai"] = rawCollect[-1]
                    full_list["group_name"] = rawCollect[1][1]
                full_list["admins"] = cList.copy()
                
            new_list[collect] = full_list.copy()
            
        cs.createCollectView(new_list)
        
        sleep(TIME_CHECK_COLLECTS)
        

vk = vk()
ts = ts()
cs = cs()

vkWall = threading.Thread(target=vk.monitorWall)
vkWall.start()

sheetTags = threading.Thread(target=addNewUsers)
sheetTags.start()

sheetCollects = threading.Thread(target=checkCollects)
sheetCollects.start()


