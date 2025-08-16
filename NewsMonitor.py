import threading
from APIs.VkApi.VkInterface import VkApi as vk
from traceback import print_exc
from time import sleep
from APIs.NewsApi.sites.YouLoveItApi import YouLoveItApi
from APIs.NewsApi.sites.KurobasInfoApi import KurobasInfoApi
import math
from confings.Messages import Messages
from Logger import logger_news
from SQLS.DB_Operations import insertNewSeenNews, getNotSeenNews
from APIs.NewsApi.NewsParentClass import NewsParentClass
from confings.Consts import PathsConsts, NewsConsts
import json
from APIs.utils import createItemPairs, local_image_upload, createCollage

def monitorNews(rcpns, theme, newsInstance:NewsParentClass):
    items = []
    while True:
        try:
            items = newsInstance.getNews()
            logger_news.info(f"[SEEN-{theme}] len {len(items)} news")
            items = getNotSeenNews(news_ids = items, origin = newsInstance.origin)
            if items:
                for item in items:
                    sleep(1.5)
                    itemInfo = newsInstance.getNewsInfo(id = item)
                    mes = Messages.formNewsMes(theme = theme, newsItem = itemInfo)
                    if len(itemInfo.images_list) > 10:
                        raw_pics_lists = createItemPairs(items = itemInfo.images_list, message_img_limit = math.ceil(len(itemInfo.images_list)/10)) 
                        pics = []
                        for raw_pics_list in raw_pics_lists:
                            collage_pics = []
                            for raw_pic in raw_pics_list:
                                collage_pics.append(local_image_upload(url = raw_pic, tag = f'collage_{theme}', isFullPathNeeded = True))
                            pics.append(createCollage(imagePaths = collage_pics, imagesPerRow = 2))
                    else:
                        pics = itemInfo.images_list
                    vk.sendMes(mess = mes, users = rcpns, tag = theme, pic = pics)
                    logger_news.info(f"[MESSAGE-{theme}] Отправлено сообщение {item}")
                insertNewSeenNews(news_ids = items, origin = newsInstance.origin)
        except Exception as e:
            logger_news.info(f"\n[ERROR-{theme}] {e} - {print_exc()}\n Последние айтемы теперь: {items}\n")
            print(e)
            print(print_exc())
            sleep(18000)   
            continue
        sleep(18000)
        

if __name__ == "__main__":
    vk = vk()
    with open(PathsConsts.NEWS_MONITOR_CONF_PATH, "r") as f: 
        conf_list = json.load(f)

    originsInstances = {
        NewsConsts.NewsOrigin.kurobasInfo: KurobasInfoApi,
        NewsConsts.NewsOrigin.youloveit: YouLoveItApi
    }
    
    threads = []
    for conf in conf_list:
        threads.append(threading.Thread(target=monitorNews, args=(conf["rcpns"], conf["theme"], originsInstances[conf["origin"]])))
    for thread in threads:
        thread.start()
        sleep(10)