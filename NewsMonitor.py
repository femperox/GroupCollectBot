import threading
from APIs.VkApi.VkInterface import VkApi as vk
from traceback import print_exc
from time import sleep
from APIs.NewsApi.YouLoveItApi import YouLoveItApi
import math
from confings.Messages import Messages
from Logger import logger_news
from SQLS.DB_Operations import insertNewSeenNews, getNotSeenNews
from confings.Consts import PathsConsts
import json
from APIs.utils import createItemPairs, local_image_upload, createCollage

def monitorNews(rcpns, theme):
    items = []
    while True:
        try:
            items = YouLoveItApi.getNews()
            logger_news.info(f"[SEEN-{theme}] len {len(items)} news")
            items = getNotSeenNews(news_ids = items, origin = YouLoveItApi.origin)
            if items:
                for item in items:
                    itemInfo = YouLoveItApi.getNewsInfo(id = item)
                    sleep(0.5)
                    mes = Messages.formNewsMes(theme = theme, newsItem = itemInfo)
                    if len(itemInfo['imgs']) > 10:
                        raw_pics_lists = createItemPairs(items = itemInfo['imgs'], message_img_limit = math.ceil(len(itemInfo['imgs'])/10)) 
                        pics = []
                        for raw_pics_list in raw_pics_lists:
                            collage_pics = []
                            for raw_pic in raw_pics_list:
                                collage_pics.append(local_image_upload(url = raw_pic, tag = 'collage', isFullPathNeeded = True))
                            pics.append(createCollage(imagePaths = collage_pics, imagesPerRow = 2))
                    else:
                        pics = itemInfo['imgs']
                    vk.sendMes(mess = mes, users = rcpns, tag = theme, pic = pics)
                    logger_news.info(f"[MESSAGE-{theme}] Отправлено сообщение {item}")
                insertNewSeenNews(news_ids = items, origin = YouLoveItApi.origin)
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
    
    threads = []
    for conf in conf_list:
        threads.append(threading.Thread(target=monitorNews, args=(conf["rcpns"], conf["theme"])))
    for thread in threads:
        thread.start()