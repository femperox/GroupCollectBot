import vk_api
from traceback import print_exc
import requests
import os
import random
import json
from pprint import pprint
import re
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from confings.Messages import MessageType, Messages
from Logger import logger, logger_fav
from SQLS.DB_Operations import addFav, getFav, deleteFav, getFandoms, getTags, addBans, insertUpdateParcel, addBannedSellers
from JpStoresApi.yahooApi import getAucInfo
from confings.Consts import CURRENT_POSRED, BanActionType, MAX_BAN_REASONS, RegexType, PayloadType, VkCommands, PRIVATES_PATH, VkCoverSize, Stores
from APIs.utils import getMonitorChats, getFavInfo, getStoreMonitorChats, flattenList
from APIs.pochtaApi import getTracking
from JpStoresApi.StoreSelector import StoreSelector

class VkApi:

    def __init__(self) -> None:
        tmp_dict = json.load(open(PRIVATES_PATH, encoding='utf-8'))
        self.__tok = tmp_dict['access_token']
        self.__group_id = tmp_dict['group_id']
        auth_data = self._login_pass_get(tmp_dict)
        if auth_data[0] and auth_data[1]:
            self.__vk_session = vk_api.VkApi(
                auth_data[0],
                auth_data[1],
                auth_handler=self._two_factor_auth
            )
        self.__vk_session.auth(token_only=True)
        self.vk = self.__vk_session.get_api()
        
        self._init_tmp_dir()
        self.__admins = tmp_dict['admins']
        
        vk_session = vk_api.VkApi(token=self.__tok)
        self.__vk_message = vk_session.get_api()
        

        self.lang = 100
    
    def _init_tmp_dir(self) -> None:
        """Создание директории для сгрузки изображений
        """
        if not os.path.isdir(os.getcwd()+'/tmp'):
            os.mkdir(os.getcwd()+'/tmp')

    def _two_factor_auth(self):
        """Двухфакторная аутентификация

        Returns:
            string, bool: ключ и запоминание устройства
        """
        key = input("Enter authentication code: ")
        remember_device = True
        return key, remember_device

    def _create_encrypt_key(self, privates: dict) -> str:
        """Создаёт или получает ключ для шифрования / дешифрования

        Args:
            privates (dict): json-словарь из файла с настройками доступа

        Returns:
            str: Ключ или ''
        """
        try:
            if privates.get('secret_key', '') == '':
                size = random.randint(5, 10)
                key = ''
                for _ in range(size):
                    key += chr(random.randint(0, 10000))
                privates.setdefault('secret_key', key)
                json.dump(privates, open(PRIVATES_PATH, 'w'))
            return privates.get('secret_key', '')
        except:
            print_exc()
            return ''
    
    def _encode_decode_str(self, key: str, string: str, encode=True) -> str:
        """Кодирует или декодирует строку по ключу

        Args:
            key (str): Ключ
            string (str): Строка для кодирования / декодирования
            encode (bool, optional): При encode=True - кодирует, иначе декодирует string

        Returns:
            str: Кодированое или декодированное значение string 
        """
        try:
            result = ''
            sign = 1 if encode else -1
            if key:
                counter = 0
                for char in string:
                    if counter == len(key):
                        counter = 0
                    result += chr(ord(char) + ord(key[counter]) * sign)
                    counter += 1
            return result
        except:
            print_exc()
            return ''
    
    def _login_pass_get(self, privates: dict) -> tuple:
        """Получает пару логин и пароль Вконтакте из файла настроек доступа

        Args:
            privates (dict): Настройки доступа

        Returns:
            tuple: Пара - логин и пароль или (None, None)
        """
        try:
            login = privates.get('login', '')
            password = privates.get('password', '')
            key = self._create_encrypt_key(privates)
            
            privates.setdefault('secret_key', key)
            if login == '' and password == '':
                # Поменять по надобности
                # ======================
                print('login:')
                new_login = input()
                print('password:')
                new_pass = input()
                # ======================
                login = self._encode_decode_str(key, new_login)
                password = self._encode_decode_str(key, new_pass)
                privates.setdefault('login', login)
                privates.setdefault('password', password)

                json.dump(privates, open(PRIVATES_PATH, 'w'))
                return new_login, new_pass
            new_login = self._encode_decode_str(key, login, encode=False)
            new_pass = self._encode_decode_str(key, password, encode=False)
            return new_login, new_pass
        except:
            print_exc()
            return None, None
        
    def _get_image_extension(self, url):
        """Получить формат файла изображения

        Args:
            url (string): путь до файла

        Returns:
            string: формат файла
        """
        extensions = ['.png', '.jpg', '.jpeg', '.gif']
        for ext in extensions:
            if ext in url:
                return ext
        return '.jpg'

    def _local_image_upload(self, url: str, tag:str) -> str:
        """Функция скачивает изображение по url и возвращает строчку с полученным именем файла

        Args:
            url (str): Ссылка на изображение

        Returns:
            str: Имя файла или пустая строка
        """
        try:
            extention = self._get_image_extension(url)
            filename = ''
            if extention != '':
                filename = 'new_image'+ tag + extention
                response = requests.get(url)
                image = open(os.getcwd()+'/VkApi/tmp/' + filename, 'wb')
                image.write(response.content)
                image.close()
            return filename
        except:
            print_exc()
            return ''

    def _cover_image_upload(self, image_name: str) -> dict:
        """Загружает локальное изображение на сервера Вконтакте

        Args:
            image_name (str): Имя файла с изображением

        Returns:
            dict: В случае успешного выполнения запроса вернёт словарь с представлением медиа Вконтакте
        """
        if image_name != '':
            vk_response = self.vk.photos.getOwnerCoverPhotoUploadServer(
                group_id= self.__group_id,
                crop_x= VkCoverSize.crop_x,
                crop_y= VkCoverSize.crop_y,
                crop_x2= VkCoverSize.crop_x2,
                crop_y2= VkCoverSize.crop_y2
            )
            vk_url = vk_response['upload_url']
            try:
                vk_response = requests.post(
                    vk_url, 
                    files={'photo': open(os.getcwd()+'/VkApi/covers/{}'.format(image_name), 'rb')}
                ).json()

                if vk_response['photo']:

                    vk_image = self.vk.photos.saveOwnerCoverPhoto(
                        photo=vk_response['photo'],
                        hash=vk_response['hash'],
                    )
          
                    return vk_image
            except:
                print_exc()
                return {}
        return {}


    def _vk_image_upload(self, image_name: str, user: str) -> dict:
        """Загружает локальное изображение на сервера Вконтакте

        Args:
            image_name (str): Имя файла с изображением

        Returns:
            dict: В случае успешного выполнения запроса вернёт словарь с представлением медиа Вконтакте
        """
        if image_name != '':

            vk_response = self.vk.photos.getMessagesUploadServer(
                peer_id= user
            )
            vk_url = vk_response['upload_url']
       
            try:
                vk_response = requests.post(
                    vk_url, 
                    files={'photo': open(os.getcwd()+'/VkApi/tmp/{}'.format(image_name), 'rb')}
                ).json()
                os.remove(os.getcwd()+'/VkApi/tmp/' + image_name)

                if vk_response['photo']:

                    vk_image = self.vk.photos.saveMessagesPhoto(
                        photo=vk_response['photo'],
                        server=vk_response['server'],
                        hash=vk_response['hash'],
                    )
          
                    return vk_image[0]
            except:
                print_exc()
                return {}
        return {}

    def _form_images_request_signature(self, image_urls: list, user, tag) -> str:
        """Получает строку для опубликования медиа-вложений

        Args:
            image_urls (list): Список url-ссылок на изображения

        Returns:
            str:  Возвращает пустую строку или строку вида <type><owner_id>_<media_id>
        """
        result = ''
        result_urls = []
        try:
            urls_count = len(image_urls)
            for i in range(urls_count):
                new_image = self._local_image_upload(image_urls[i], tag)
                if new_image != '':
                    vk_image = self._vk_image_upload(new_image, user)
               
                    if vk_image != {}:
                        result += 'photo{}_{}_{}'.format(vk_image['owner_id'], vk_image['id'], vk_image['access_key']) + ('' if i == urls_count - 1 else ',')
                        result_urls.append(vk_image['sizes'][-1]['url'])
            if result != '':
                if result[len(result) - 1] == ',':
                    result[:len(result) - 1:]

            return result, result_urls
        except:
            print_exc()
            return '', []

    def _get_albums(self):
        """Получить альбомы сообщества

        Returns:
            list of dict: список альбомов и инфа о них
        """

        albums = self.vk.photos.getAlbums(owner_id = f'-{self.__group_id}', need_system=1)
        
        return albums

        
    def get_name(self, id):
        '''
        Получить имя, фамилию и числовой айди пользователя

        :param id: ссылка на пользователя в произвольном формате
        :return:
        '''

        user = self.vk.users.get(user_ids = id, lang = self.lang)
        return "@id{0}({1})".format(user[0]['id'], user[0]['first_name']+' '+user[0]['last_name'])   
    
    def get_id(self, id):
        '''
        Получить числовой айди пользователя

        :param id: ссылка на пользователя в произвольном формате
        :return:
        '''

        return self.vk.users.get(user_ids = id, lang = self.lang)[0]['id']

    def get_group_id(self, id):
        '''
        Получить числовой айди группы

        :param id: ссылка на группу в произвольном формате
        :return:
        '''

        return self.vk.groups.getById(group_id = id, lang = self.lang)[0]['id']
    
    def get_group_name(self, id):
        '''
        Получить имя, фамилию и числовой айди пользователя

        :param id: ссылка на пользователя в произвольном формате
        :return:
        '''

        group = self.vk.groups.getById(group_id = id, lang = self.lang)
        return "@club{0}({1})".format(group[0]['id'], group[0]['name']) 
    
    def get_message(self, chat_id, mess_id):
        """Получить инфо о сообщении в чате

        Args:
            chat_id (int): id чата
            mess_id (int): id сообщения

        Returns:
            dict: словарь информации о сообщении
        """

        params = {
                'group_id': self.__group_id,
                'peer_id': chat_id,
                'conversation_message_ids': mess_id,
            }
        
        return self.__vk_message.messages.getByConversationMessageId(**params)
    
    def removeChatUser(self, chat, user):
        """удалить пользователя из чата

        Args:
            chat (int): id чата
            user (int): id пользователя
        """
           
        params = { 'chat_id': chat % 2000000000,
                   'user': user, 
                   'member_id': user
                 }
        self.__vk_message.messages.removeChatUser(**params)


    def form_inline_buttons(self, type, items = ''):

            settings = dict(one_time=False, inline=True)
            
            keyboard = ''

            if type == MessageType.monitor_big_category:  
                      
                keyboard = VkKeyboard(**settings)
                keyboard.add_callback_button(label='Забанить продавца', color=VkKeyboardColor.NEGATIVE, payload=PayloadType.ban_seller)
                keyboard.add_callback_button(label='Добавить в избранное', color=VkKeyboardColor.POSITIVE, payload=PayloadType.add_fav)
            
            elif type in [MessageType.monitor_big_category_other, MessageType.monitor_seller, MessageType.fav_list]:
        
                keyboard = VkKeyboard(**settings)
                j = 0
                columnn_count = 2
                for i in range(len(items)):
                    
                    if j % columnn_count == 0 and j!=0:
                        keyboard.add_line()

                    if type in [MessageType.monitor_big_category_other, MessageType.monitor_seller]:
                        payload = {"type": PayloadType.add_fav_num["type"], "text": PayloadType.add_fav_num["text"].format(i)}
                        keyboard.add_callback_button(label=f'Избранное {i+1}', color=VkKeyboardColor.POSITIVE, payload=payload)
                    
                    elif type in [MessageType.fav_list]:
                        payload = {"type": PayloadType.delete_fav_num["type"], "text": PayloadType.delete_fav_num["text"].format(i)}
                        keyboard.add_callback_button(label=f'Удалить {i+1}', color=VkKeyboardColor.NEGATIVE, payload=payload)

                    j += 1



            return keyboard

    def sendMes(self, mess, users, tag = '', pic = [], keyboard = False):
        """Отправка сообщения

        Args:
            mess (string): сообщение для отправки
            users (list of string): получатели сообщения
            tag (str, optional): тэг для сохранения пикч. Defaults to ''.
            pic (list, optional): список пикч для сообщения. Defaults to [].
            type (MessageType, optional): тип сообщения. Для inline-кнопок. Defaults to MessageType.monitor_store.
        """

        try:          
            
            params = {
                'group_id': self.__group_id,
                'peer_ids': users,
                'message': mess,
                'random_id': 0,
            }

            if keyboard: params['keyboard'] = keyboard.get_keyboard()

            if pic != []:
                if re.search(RegexType.regex_vk_photo_scheme, pic[0]):
                    params.setdefault('attachment', pic[0])
                else:    
                    attachments = self._form_images_request_signature(pic, self.__group_id, tag)
                    if attachments != ('', []):
                        params.setdefault('attachment', attachments[0])

            self.__vk_message.messages.send(**params) 

        except Exception as e:
            print_exc()
    
        
    def get_attachemetns(self, peer_id, conv_id, idx):
        """Получение вложения из сообщения

        Args:
            peer_id (int): id отправителя сообщения
            conv_id (int): id сообщения
            idx (int): индекс искомой фотографии

        Returns:
            string: ссылка на фото на сервере вк
        """
        
        params = {
            'group_id': self.__group_id,
            'peer_id': peer_id,
            'conversation_message_ids': conv_id,
        }

        result = self.__vk_message.messages.getByConversationMessageId(**params)
        
        return result['items'][0]['attachments'][idx]['photo']
    
    def get_chat_members(self, chat_id):
        """Получить список пользователей чата

        Args:
            chat_id (int): id чата

        Returns:
            list of int: список id участников беседы
        """

        params = {
            'peer_id': chat_id,
        }
        
        result = self.__vk_message.messages.getConversationMembers(**params)
        result = [profile['id'] for profile in result['profiles']]

        return result

    def is_group_members(self, user_id):
        """Получить список пользователей сообщества

        Returns:
            list of int: список id участников сообщества
        """

        params = {
            'group_id': self.__group_id,
            'user_id': user_id
        }
        
        result = self.vk.groups.isMember(**params)
    
        return result

    
    def monitorGroupActivity(self):
       """Мониторинг активности группы
       """
       
       vkBotSession = vk_api.VkApi(token=self.__tok)
       longPoll = VkBotLongPoll(vkBotSession, self.__group_id)
       whiteList = [int(x) for x in self.__admins]

       storeSelector = StoreSelector()
        
       while True:
        try:
            for event in longPoll.listen():  

                # Выход из сообщества - кик из бесед
                if event.type == VkBotEventType.GROUP_LEAVE:
                    leave_user = event.obj['user_id']
                    
                    chat_members_list = {}
                    [ chat_members_list.update({x: self.get_chat_members(chat_id = x)}) for x in getStoreMonitorChats()]

                    for chat in chat_members_list.keys():
                        if leave_user in chat_members_list[chat]:
                            self.sendMes(mess = Messages.userChatRemovalLeaveMess(user = self.get_name(leave_user)), users= [chat])
                            self.removeChatUser(user = leave_user, chat = chat)
                
                # Исходящие сообщения
                elif event.type == VkBotEventType.MESSAGE_REPLY:
                    sender = event. obj['from_id']
                    chat = event.obj['peer_id']
 
                    # Личные сообщение
                    not_dm_chats = getMonitorChats()
                    not_dm_chats.append(getStoreMonitorChats())
                    if chat not in not_dm_chats:
                        try:
                            track = re.findall(RegexType.regex_track, event.obj['text'])[0]
                            tracking_info = getTracking(track)
                            tracking_info['rcpnVkId'] = chat

                            insertUpdateParcel(tracking_info)          
                        except:
                            continue   

                       
                elif event.type ==VkBotEventType.MESSAGE_EVENT:

                    # Действия с сообщениями - callback кнопицы 
                    if 'payload' in event.object.keys():

                        chat = event.object['peer_id']
                        message_id = event.object['conversation_message_id']                    
                        mes = self.get_message(chat_id = chat, mess_id= message_id)

                        # добавление в избранное
                        if event.object['payload']['type'] == PayloadType.add_fav['type']:

                            item_index = int(event.object['payload']['text'])
                            fav_item = getFavInfo(mes['items'][0]['text'], item_index)

                            fav_item['usr'] = event.object['user_id']
                            try:
                                fav_item['attachement'] = mes['items'][0]['attachments'][item_index]['photo']
                            except:
                                fav_item['attachement'] = self.get_attachemetns(peer_id=chat, conv_id=message_id, idx = item_index)
                                
                            fav_item['attachement'] = 'photo{}_{}_{}'.format(fav_item['attachement']['owner_id'], fav_item['attachement']['id'], fav_item['attachement']['access_key'])
                            
                            mess = Messages.mes_fav(fav_item = fav_item, fav_func = addFav).format(self.get_name(fav_item['usr']), f"{fav_item['store_id']}_{fav_item['id']}")
                            
                            logger_fav.info(f"[ADD_FAV-{fav_item['usr']}] для пользователя {fav_item['usr']}: {mess}")
                            self.sendMes(mess = mess, users = chat)

                        # удаление избранного
                        elif event.object['payload']['type'] == PayloadType.delete_fav_num['type']:

                            item_index = int(event.object['payload']['text'])
                            auc_id = re.findall(RegexType.regex_hashtag, mes['items'][0]['text'])
                            auc_id = [auc for auc in auc_id if auc not in VkCommands.hashtagList][item_index].replace('#', '')  
                                             
                            mes = Messages.mes_delete_fav(user_name = self.get_name(event.object['user_id']), user_id = event.object['user_id'], auc_id = auc_id, delete_func = deleteFav )
                            
                            logger_fav.info(f"[DELETE_FAV-{event.object['user_id']}] для пользователя {event.object['user_id']}: {mes}")
                            
                            self.sendMes(mess=mes, users=chat)                       
                        
                        # бан продавана
                        elif event.object['payload'] == PayloadType.ban_seller and str(event.object['user_id']) in self.__admins:

                            category = re.findall(RegexType.regex_hashtag, mes['items'][0]['text'])

                            seller = category[-1].replace('#', '')
                            category = category[0].replace('#', '')

                            if seller:

                                storeSelector.url = re.findall(RegexType.regex_store_item_id_url, mes['items'][0]['text'])[0]

                                isBanned = addBannedSellers(category = category.split("_")[-1], seller_id = seller, store_id = storeSelector.getStoreName())

                                message = Messages.mes_ban(seller = seller, category = category, isBanned = isBanned)
                                self.sendMes(mess = message, users= chat)
                                if not isBanned:
                                    logger.info(f"\n[BAN-{category.split('_')[-1]}] Забанен продавец {seller}\n")                      


                        params = {
                            'user_id': event.object.user_id,
                            'peer_id': event.object.peer_id,
                            'event_id': event.object.event_id,              
                        }                 

                        self.__vk_message.messages.sendMessageEventAnswer(**params) 

                    
                # Входящие сообщения
                elif event.type == VkBotEventType.MESSAGE_NEW:

                    sender = event.obj.message['from_id']
                    chat = event.obj.message['peer_id']
                    user_name = self.get_name(sender)

                    # Если человек вступил в чат, но не состоит в обществе:
                    if 'action' in event.obj.message and event.object.message['action']['type'] in ['chat_invite_user', 'chat_invite_user_by_link']:
       
                        invited_user = event.object.message['action']['member_id']

                        if not self.is_group_members(user_id = invited_user):
                            self.sendMes(mess = Messages.userChatRemovalLeaveMess(user = self.get_name(invited_user)), users= [chat])
                            self.removeChatUser(user = invited_user, chat = chat)
                    
                    # Удаление спамера из чата по магазинам
                    elif chat in getStoreMonitorChats() and sender not in whiteList:
                        
                        self.sendMes(mess = Messages.userCharRemovalMess(user = user_name), users= [chat])
                        self.removeChatUser(user = sender, chat = chat)
                               
                    elif 'reply_message' in event.obj.message and str(event.obj.message['from_id'])[1:] != self.__group_id:
                                              
                        # Бан продавца
                        if str(sender) in self.__admins and event.obj.message['text'].lower() in VkCommands.banList:

                            try:
                                reply = event.obj.message['reply_message']['text']   
                                store_id = ''
                                seller = ''
                                # в посте с товаров два тега: тег_категории и тег_продавца
                                category = re.findall(RegexType.regex_hashtag, reply)


                                if VkCommands.hashtagList[0] in category or len(category)==1 or VkCommands.hashtagList[1] in category:
                                    continue

                                if category[0].split('_')[0].lower()[1:] == Stores.mercari_rus:

                                    seller = re.findall(RegexType.regex_hard_seller_name, reply)[0].split(' ')[-1].replace('(','').replace(')','')
                                    category = category[0][1:]
                                    store_id = Stores.mercari
                                else:

                                    seller = category[-1][1:]
                                    category = category[0].split("_")[-1]
                                    store_id = Stores.yahooAuctions

                                if seller:
                                    isBanned = addBannedSellers(category = category, seller_id = seller, store_id=store_id)

                                    message = Messages.mes_ban(seller = seller, category = category, isBanned = isBanned)
                                    self.sendMes(mess = message, users= chat)
                                    if not isBanned:
                                        logger.info(f"\n[BAN-{category}] Забанен продавец {seller}\n")
                            except:
                                continue

                    # получение избранного        
                    elif event.obj.message['text'].lower().split(' ')[0] in VkCommands.getFavList:
                            
                            try:
                                text = event.obj.message['text'].lower()
                                offset = 0
                                if len(text.split(' '))>1 and text.split(' ')[1].isdigit():
                                    offset = int(text.split(' ')[1]) - 1
                                    
                                favListing = getFav(sender, offset)
                                
                                pics = []
                                keyboard = self.form_inline_buttons(type = MessageType.fav_list, items = favListing[0])
                                mess, picStr = Messages.formFavMes(user_name=user_name, favListing= favListing, offset= offset)
                               
                                if picStr != '': pics.append(picStr)
                                
                                logger_fav.info(f"[SEL_FAV-{sender}] для пользователя {sender} выведен список избранного: {','.join([item[1] for item in favListing[0]])}")
                                
                                self.sendMes(mess=mess, users=chat, pic=pics, keyboard = keyboard)
                            except Exception as e:
                                pprint(e)
                                logger_fav.info(f"[ERROR_SEL_FAV-{sender}] для пользователя {sender}: {e}") 
                                            
                    # Ручное добавление в избранное 
                    elif event.obj.message['text'].lower().split(' ')[0] in VkCommands.favList and event.obj.message['text'].lower().find("https://")>=0:
                        
                        auc_ids = re.findall(RegexType.regex_store_item_id_url, event.obj.message['text'].lower())  
                        
                        items = []
                        for id in auc_ids:
                            info = {}
                            info = storeSelector.selectStore(id)
                            storeSelector.url =id
                            info['attachement'] = self._form_images_request_signature([info['mainPhoto']], self.__group_id, tag="custom_fav")[0]
                            info['usr'] = sender
                            info['id'] = storeSelector.getItemID() 
                            info['date_end'] = info['endTime']
                            info['store_id'] = storeSelector.getStoreName()

                            items.append(info.copy())

                        mess = Messages.mes_add_fav(user_name=user_name, auc_list=items, add_func=addFav)
                        self.sendMes(mess, chat)


                # репосты
                elif event.type == VkBotEventType.WALL_POST_NEW and 'copy_history' in event.object:
                    
                    post_id = event.obj['id']
                    self.edit_wall_post(VkCommands.repost_tag, post_id = post_id)

                # новые записи (автотеги)    
                elif event.type == VkBotEventType.WALL_POST_NEW:
                    post = {}
                    post['text'] = event.obj['text']
                    post['id'] = event.obj['id']
                    post['tags'] = re.findall(RegexType.regex_hashtag, post['text'])

                    allFandoms = getFandoms()
                    mess = 'Автотеги.'
                    
                    isTagPost = False
                    
                    for tag in post['tags']:
                        if tag.replace('#','').replace(VkCommands.group_tag, '') in allFandoms:
                            isTagPost = True
                            users = getTags(tag.replace('#','').replace(VkCommands.group_tag, ''))
                            users = '\n'.join([self.get_name(usr) for usr in users])
                            #users = '\n'.join(str(usr) for usr in users)
                            mess += f'\n\n{tag}:\n{users}'
                    
                    if isTagPost:
                        self.post_wall_comment(mess=mess, post_id=post['id'])
                
                # удаление комментариев
                elif  event.type in [VkBotEventType.PHOTO_COMMENT_DELETE, VkBotEventType.WALL_REPLY_DELETE] and event.object['deleter_id'] not in whiteList:
                    
                    deleter_id = event.object['deleter_id'] if event.object['deleter_id'] != 100 else event.object['user_id']

                    count_bans = addBans(deleter_id, BanActionType.deleting.value)

                    if count_bans >= MAX_BAN_REASONS:
                        self.ban_users({'id': deleter_id, 'comment': 'Удаление комментариев.'})

                    mess = Messages.mes_ban_user_delete.format(self.get_name(deleter_id),count_bans)

                    if event.type == VkBotEventType.WALL_REPLY_DELETE:
                        self.post_wall_comment(mess = mess, post_id = event.object['post_id'])
                    else:
                        self.post_photo_comment(mess = mess, photo_id = event.object['photo_id'])

                # изменение комментариев
                elif  event.type in [VkBotEventType.PHOTO_COMMENT_EDIT, VkBotEventType.WALL_REPLY_EDIT] and event.object['from_id'] not in whiteList:
                    deleter_id = event.object['from_id']

                    count_bans = addBans(deleter_id, BanActionType.editing.value)
                    if count_bans >= MAX_BAN_REASONS:
                        self.ban_users({'id': deleter_id, 'comment': 'Изменение комментариев.'})
                    
                    mess = Messages.mes_ban_user_edit.format(self.get_name(deleter_id),count_bans)

                    if event.type == VkBotEventType.WALL_REPLY_EDIT:
                        self.post_wall_comment(mess = mess, post_id = event.object['post_id'])
                    else:
                        self.post_photo_comment(mess = mess, photo_id = event.object['photo_id'])            
                        
        except Exception as e:
            pprint(e)
            print_exc()
            continue
    
    def edit_group_status(self, mess): 
        """Изменить статус сообщества

        Args:
            mess (string): текст нового статуса
        """

        try:
            params = {
                'group_id': self.__group_id,
                'text': mess,
            }

            self.vk.status.set(**params)

        except Exception as e:
            print_exc()

    def get_wall_post(self, post_owner_id):
        """получить инфо о посте

        Args:
            post_owner_id (string): Перечисленные через запятую идентификаторы, которые представляют собой идущие через знак подчеркивания ID владельцев стен и ID самих записей на стене.

        Returns:
            dict: информация о записи
        """

        try:
            params = {
                'posts': post_owner_id,
            }

            res = self.vk.wall.getById(**params)
            return res

        except Exception as e:
            print_exc()        

    def edit_wall_post(self, mess, post_id):
        """изменить запись на стене

        Args:
            mess (string): текст
            post_id (_type_): id поста
        """
        
        try:
            params = {
                'owner_id': f'-{self.__group_id}',
                'post_id': post_id,
                'message': mess
            }

            self.vk.wall.edit(**params)

        except Exception as e:
            print_exc()

    def post_wall_comment(self, mess, post_id, from_group=1):
        """оставить комментарий под записью

        Args:
            mess (string): текст
            post_id (int): id поста
            from_group (int, optional): от лица группы. Defaults to 1
        """

        try:
            params = {
                'owner_id': f'-{self.__group_id}',
                'post_id': post_id,
                'message': mess,
                'from_group': from_group,
                'guid': 0,
            }

            self.__vk_message.wall.createComment(**params)

        except Exception as e:
            print_exc()
    
    def post_photo_comment(self, mess, photo_id, from_group=1):
        """оставить комментарий под фотографией

        Args:
            mess (string): текст
            photo_id (int): id фото
            from_group (int, optional): от лица группы. Defaults to 1.
        """

        try:
            params = {
                'owner_id': f'-{self.__group_id}',
                'photo_id': photo_id,
                'message': mess,
                'from_group': from_group,
                'guid': 0,
            }

            self.vk.photos.createComment(**params)

        except Exception as e:
            print(e)
            print_exc()

    
    def ban_users(self, userBanReason):
        """Бан пользователей

        Args:
            userBanReason (dict): словарь с инфой о забаненных людей
        """

        try:
            params = {
            'group_id': self.__group_id,
            'comment_visible': 1
            }

            params['owner_id'] = userBanReason['id']
            params['comment'] = userBanReason['comment']

            self.vk.groups.ban(**params)    

        except Exception as e:
            print(e)
            print_exc()        
