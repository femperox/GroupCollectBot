from APIs.VkApi.VkInterface import VkApi as vk
from Logger import logger_utils
from traceback import print_exc
import threading

threads = []
try:
    vk = vk()

    vkWall = threading.Thread(target=vk.monitorGroupActivity)
    vkWall.start()

    vkChat = threading.Thread(target=vk.monitorChatActivity, args=(logger_utils,))
    vkChat.start()
    
except Exception as e:
    logger_utils.info(f"[ERROR_UTILS] {e} {print_exc()}")   


