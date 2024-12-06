import vk_api
from traceback import print_exc
import requests
import os
import random
import json
from pprint import pprint
from datetime import datetime
import re
from random import randint
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.longpoll import VkLongPoll, VkChatEventType, VkEventType, VkLongpollMode
from confings.Messages import MessageType, Messages
from Logger import logger, logger_fav, logger_utils
from SQLS.DB_Operations import addFav, getFav, deleteFav, getFandoms, getTags, addBans, insertUpdateParcel, addBannedSellers, updateUserMenuStatus, getUserMenuStatus, getUserMenuCountry
from confings.Consts import VkTopicCommentChangeType, TrackingTypes, ItemBuyStatus, VK_PROPOSED_CHAT_ID, VK_ERRORS_CHAT_ID, BanActionType, MAX_BAN_REASONS, RegexType, PayloadType, VkCommands, PRIVATES_PATH, VkCoverSize, Stores, PayloadPriceCheckCountry
from APIs.utils import getMonitorChats, getFavInfo, getStoreMonitorChats
from APIs.TrackingAPIs.TrackingSelector import TrackingSelector
from APIs.StoresApi.JpStoresApi.StoreSelector import StoreSelector
from VkApi.objects.VkButtons import VkButtons
import time

class VkApi:

    def __init__(self, key_token = 'access_token', key_group_id = 'group_id') -> None:
        tmp_dict = json.load(open(PRIVATES_PATH, encoding='utf-8'))
        
        self.__tok = tmp_dict[key_token]
        self.__group_id = tmp_dict[key_group_id]

        auth_data = self._login_pass_get(tmp_dict)
        if auth_data[0] and auth_data[1]:
            self.__vk_session = vk_api.VkApi(
                auth_data[0],
                auth_data[1],
                auth_handler=self._two_factor_auth,
                captcha_handler=self.captcha_handler 
            )
        self.__vk_session.auth(token_only=True)
        self.vk = self.__vk_session.get_api()
        
        self._init_tmp_dir()
        self.__admins = tmp_dict['admins']
        
        vk_session = vk_api.VkApi(token=self.__tok)
        self.__vk_message = vk_session.get_api()
        

        self.lang = 100

    def get_token(self):
        return self.__tok
    
    def get_current_group_id(self):
        return self.__group_id
    
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
                filename = f'new_image{randint(0,15000)}_{tag}' + extention
                response = requests.get(url)
                image = open(os.getcwd()+'/VkApi/tmp/' + filename, 'wb')
                image.write(response.content)
                image.close()
            return filename
        except:
            print_exc()
            self._local_image_upload(url, tag)

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
    
    def _vk_image_upload(self, image_name: str, user: str, isWallServer = False) -> dict:
        """Загружает локальное изображение на сервера Вконтакте

        Args:
            image_name (str): Имя файла с изображением

        Returns:
            dict: В случае успешного выполнения запроса вернёт словарь с представлением медиа Вконтакте
        """
        if image_name != '':
            if isWallServer:
                vk_response = self.vk.photos.getWallUploadServer(group_id=self.__group_id)
            else:
                vk_response = self.vk.photos.getMessagesUploadServer()
            
            vk_url = vk_response['upload_url']
            try:
                vk_response = requests.post(
                    vk_url, 
                    files={'photo': open(os.getcwd()+'/VkApi/tmp/{}'.format(image_name), 'rb')}
                ).json()
                os.remove(os.getcwd()+'/VkApi/tmp/' + image_name)

                if vk_response['photo']:
                    if isWallServer:
                        vk_image = self.vk.photos.saveWallPhoto(
                            group_id=self.__group_id,
                            photo=vk_response['photo'],
                            server=vk_response['server'],
                            hash=vk_response['hash'],                            
                        )
                    else:

                        vk_image = self.vk.photos.saveMessagesPhoto(
                            photo=vk_response['photo'],
                            server=vk_response['server'],
                            hash=vk_response['hash'],
                        )
                    
                    return vk_image[0]
            except Exception as e:
                pprint(e)
                print_exc()
                #self._vk_image_upload(image_name, user, isWallServer)
        return {}
    
    def _form_images_request_signature(self, image_urls: list, user, tag, isWallServer = False) -> str:
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
                time.sleep(2)
                new_image = self._local_image_upload(image_urls[i], tag)
                if new_image != '':
                    vk_image = self._vk_image_upload(new_image, user, isWallServer)
               
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

    def get_albums(self):
        """Получить базовую инфу о фотоальбомах сообщества - id и название

        Returns:
            list of dict: список словарей с инфой о фотоальбоме
        """
        try:
            albums_info = self.vk.photos.getAlbums(owner_id = f'-{self.__group_id}', need_system = 1)['items']
            result = []
            for album in albums_info:
                result.append({'title': album['title'], 
                               'id': album['id']})
            return result
        except Exception as e:
            pprint(e)
            return []

    
    def get_topics(self):
        """Получить базовую инфу об обсуждениях сообщества - id и название

        Returns:
            list of dict: список словарей с инфой об обсуждении
        """
        try:
            topics_info = self.vk.board.getTopics(group_id=self.__group_id)['items']
            result = []
            for topic in topics_info:
                result.append({'title': topic['title'], 
                               'id': topic['id']})
            return result
        except Exception as e:
            pprint(e)
            return []
        
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
    
    def get_tuple_name(self, id):
        '''
        Получить имя, фамилию и числовой айди пользователя

        :param id: ссылка на пользователя в произвольном формате
        :return:
        '''

        id = id.split('/')[-1]
        user = self.vk.users.get(user_ids = id, lang = self.lang)
        return ( "{0} {1}".format(user[0]['first_name'], user[0]['last_name']), 'https://vk.com/id{}'.format(user[0]['id']))

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
    

    def get_group_info(self, id):
        '''
        Получить имя, фамилию и числовой айди пользователя

        :param id: ссылка на пользователя в произвольном формате
        :return:
        '''

        group = self.vk.groups.getById(group_id = id, lang = self.lang)
        return group
    
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

    def sendMes(self, mess, users, tag = '', pic = [], keyboard = False, reply_to = ''):
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
                'reply_to': reply_to
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

        try:
            result = self.__vk_message.messages.getByConversationMessageId(**params)
        
            return result['items'][0]['attachments'][idx]['photo']
        except:
            return ''
    
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

    def monitorChatActivity(self, logger):
        """_summary_
        """

        vkBotSession = vk_api.VkApi(token=self.__tok)
        longPoll = VkLongPoll(vkBotSession,mode= VkLongpollMode.GET_EXTENDED, group_id = self.__group_id, wait = 50)
        whiteList = [int(x) for x in self.__admins]

        while True:
            try:
                for event in longPoll.listen():

                    if event.type == VkEventType.CHAT_UPDATE:
                        logger.info(f'[{event.type}] - {event.raw}')
                        
                        if event.update_type == VkChatEventType.USER_JOINED:
                        
                            invited_user = event.info['user_id']
                            chat = event.peer_id

                            logger.info(f'[JOINED] - {invited_user}({self.get_name(invited_user)}) joined {chat}')

                            if not self.is_group_members(user_id = invited_user):
                                logger.info(f'[KICKED] - {invited_user}({self.get_name(invited_user)}) from {chat}')
                                self.sendMes(mess = Messages.userChatRemovalLeaveMess(user = self.get_name(invited_user)), users= [chat])
                                self.removeChatUser(user = invited_user, chat = chat)                        

                    
            except Exception as e:
                pprint(e)
                print_exc()
                continue

    def monitorGroupActivity(self):
       """Мониторинг активности группы
       """
       
       vkBotSession = vk_api.VkApi(token=self.__tok)

       longPoll = VkBotLongPoll(vkBotSession, self.__group_id, wait = 50)
       whiteList = [int(x) for x in self.__admins]

       # Личные сообщение
       not_dm_chats = getMonitorChats()
       not_dm_chats.extend(getStoreMonitorChats())
       not_dm_chats.append(VK_PROPOSED_CHAT_ID)

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
 
                    if chat not in not_dm_chats:
                        try:
                            tracking_type = ''
                            for regex in RegexType.tracking_types_list:
                                track = re.match(regex, event.obj['text'])

                                if track: 
                                    tracking_type = TrackingTypes.ids[regex]
                                    break
                            tracking_info = {}
                            try:
                                tracking_info = TrackingSelector.selectTracker(track=track.group(), type=tracking_type)
                                tracking_info['rcpnVkId'] = chat 
                                tracking_info['trackingType'] = tracking_type

                                insertUpdateParcel(tracking_info)      
                                logger_utils.info(f"[INSERT-TRACK] пользователю [{chat}] выдан трек [{tracking_info['barcode']}] ")    
                            except Exception as e:
                                logger_utils.info(f"[INSERT-TRACK-ERROR] ОШИБКА: {e} - пользователю [{chat}] выдан трек [{tracking_info['barcode']}] ")   
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
                            fav_item = getFavInfo(mes['items'][0]['text'], item_index, isPosredPresent = False if 'fromBuyMenu' in event.object['payload'].keys() else True)

                            fav_item['usr'] = event.object['user_id']
                            try:
                                fav_item['attachement'] = mes['items'][0]['attachments'][item_index]['photo']
                            except:
                                fav_item['attachement'] = self.get_attachemetns(peer_id=chat, conv_id=message_id, idx = item_index)
                                
                            if fav_item['attachement']:
                                fav_item['attachement'] = 'photo{}_{}_{}'.format(fav_item['attachement']['owner_id'], fav_item['attachement']['id'], fav_item['attachement']['access_key'])
                            
                            mess = Messages.mes_fav(fav_item = fav_item, fav_func = addFav).format(self.get_name(fav_item['usr']), f"{fav_item['siteName']}_{fav_item['id']}")
                            
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
                        elif event.object['payload']['type'] == PayloadType.ban_seller_num['type'] and str(event.object['user_id']) in self.__admins:

                            item_index = int(event.object['payload']['text'])
                            category = re.findall(RegexType.regex_hashtag, mes['items'][0]['text'])

                            seller = category[1:][item_index].replace('#', '').replace(')', '')
                            category = category[0].replace('#', '')

                            if category.split('_')[0].lower() == Stores.mercari_rus:
                                store_id = Stores.mercari
                            else:
                                store_id = Stores.yahooAuctions

                            if seller:

                                isBanned = addBannedSellers(category = category, seller_id = seller, store_id = store_id)

                                message = Messages.mes_ban(seller = seller, category = category, isBanned = isBanned)
                                self.sendMes(mess = message, users= chat)
                                if not isBanned:
                                    logger.info(f"\n[BAN-{category.split('_')[-1]}] Забанен продавец {seller}\n") 

                        # менюшка с чеком цены
                        elif event.object['payload']["type"] == PayloadType.menu_check_price["type"]:

                            updateUserMenuStatus(user_id = event.object.user_id, status = PayloadType.menu_check_price['type'], country = event.object['payload']['country'])
                            self.sendMes(mess = Messages.formCalcMes(event.object['payload']['country']), users = chat)     

                        # Челик поставил на выкуп товар
                        elif event.object['payload']["type"] == PayloadType.menu_bot_add_item["type"]:

                            attachment = ''
                            if len(mes['items'][0]['attachments']) > 0:
                                attachment =  mes['items'][0]['attachments'][0]['photo']
                                attachment = 'photo{}_{}_{},'.format(attachment['owner_id'], attachment['id'], attachment['access_key'])

                            url = re.findall(RegexType.regex_store_url_bot, mes['items'][0]['text'])[0]
                            textInfo = event.object['payload']["text"].replace(url, '')
                            text = Messages.formAddItemMes(item_url = url, user = self.get_name(event.object.user_id), info = textInfo)
                            self.sendMes(mess = text, users = VK_PROPOSED_CHAT_ID, 
                                         pic = [attachment] if attachment else [],
                                         keyboard=VkButtons.form_menu_buying_buttons(userId = event.object.user_id, userMesId = mes['items'][0]['id']))

                            edit_params = {
                                'peer_id' : mes['items'][0]['peer_id'],
                                'message': mes['items'][0]['text'],
                                'group_id': self.__group_id,
                                'conversation_message_id': mes['items'][0]['conversation_message_id'],
                                'keyboard': '',
                                'attachment': attachment
                            }

                            self.__vk_message.messages.edit(**edit_params)
                            self.sendMes(mess = "Спасибо! Ваша заявка на выкуп принята!" + Messages.bot_ending, users = chat)

                        # менюшка со статусом выкупа
                        elif event.object['payload']["type"] in [PayloadType.buy_fail["type"], PayloadType.buy_succes["type"]]:

                            if event.object['payload']["type"] == PayloadType.buy_succes["type"]:
                                mess = 'Ваш товар был успешно выкуплен! Коллективщик свяжется с вами для последующей оплаты позже.'
                                itemStatus = ItemBuyStatus.succes
                            else:
                                mess = 'Ваш товар не успели выкупить/удалили/не прошла ваша ставка.'
                                itemStatus = ItemBuyStatus.fail

                            mess += Messages.bot_ending

                            attachment = ''
                            if len(mes['items'][0]['attachments']) > 0:
                                attachment =  mes['items'][0]['attachments'][0]['photo']
                                attachment = 'photo{}_{}_{},'.format(attachment['owner_id'], attachment['id'], attachment['access_key'])

                            edit_params = {
                                'peer_id' : mes['items'][0]['peer_id'],
                                'message': Messages.set_mes_buying_status(itemStatus) + mes['items'][0]['text'],
                                'group_id': self.__group_id,
                                'conversation_message_id': mes['items'][0]['conversation_message_id'],
                                'keyboard': '',
                                'attachment': attachment
                            }

                            self.__vk_message.messages.edit(**edit_params)

                            self.sendMes(mess = mess, users = event.object['payload']['user'], reply_to = event.object['payload']['userMes'])

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

                    # Удаление спамера из чата по магазинам
                    if chat in getStoreMonitorChats() and sender not in whiteList:
                        
                        self.sendMes(mess = Messages.userCharRemovalMess(user = user_name), users= [chat])
                        self.removeChatUser(user = sender, chat = chat)

                    # менюшка
                    elif chat not in not_dm_chats and event.obj.message['text'].lower() in  VkCommands.menuList:
                        # and (sender in whiteList)
                        self.sendMes(mess="Выберите пункт меню", users=chat, keyboard=VkButtons.form_menu_buttons())

                    # ответ на менюшку
                    elif PayloadType.menu_check_price["type"] == getUserMenuStatus(user_id=sender):
                        updateUserMenuStatus(user_id=sender, status= PayloadType.menu_bot_none["type"])
                        selected_country = getUserMenuCountry(user_id = sender)

                        url = event.obj.message['text']
                        try:
                            url = re.findall(RegexType.regex_store_url_bot, url)[0]  
                            messText, pic = Messages.formPriceMes(url = url, country = selected_country)
                            payload = event.obj.message['text'].split('?source=home_shops_flashsale_component')[0]
                            self.sendMes(mess = messText, users= chat, keyboard = VkButtons.form_menu_buttons(isAddButton = True, buttonPayloadText = payload), pic = [pic] if pic else [])
                            logger_utils.info(f"""[CHECK_PRICE] - Расчитана цена для пользователя {self.get_name(id = sender)} товара [{url}]""")
                        except Exception as e:
                            pprint(e)
                            logger_utils.info(f"""[ERROR_CHECK_PRICE] - Не удалось посчитать цену для пользователя {self.get_name(id = sender)} товара [{url}] :: {e}""")
                            self.sendMes(mess = "Возникла ошибка, попробуйте позже ещё раз! Убедитесь в правильности ссылки! Снова выберите в меню кнопку расчёта цены", users= chat) 
                            self.sendMes(mess = f"Сообщение:\n {url}\n\n\nОшибка:\n{e}", users=VK_ERRORS_CHAT_ID)                                 
                    
                    # получение избранного        
                    elif event.obj.message['text'].lower().split(' ')[0] in VkCommands.getFavList and sender in whiteList:
                            try:
                                text = event.obj.message['text'].lower()
                                offset = 0
                                if len(text.split(' '))>1 and text.split(' ')[1].isdigit():
                                    offset = int(text.split(' ')[1]) - 1
                                    
                                favListing = getFav(sender, offset)
                                pics = []
                                keyboard = VkButtons.form_inline_buttons(type = MessageType.fav_list, items = favListing[0]) 
                                mess, picStr = Messages.formFavMes(user_name=user_name, favListing= favListing, offset= offset)
                               
                                if picStr != '': pics.append(picStr)
                                
                                logger_fav.info(f"[SEL_FAV-{sender}] для пользователя {sender} выведен список избранного: {','.join([item[1] for item in favListing[0]])}")
                                
                                self.sendMes(mess=mess, users=chat, pic=pics, keyboard = keyboard)
                            except Exception as e:
                                pprint(e)
                                logger_fav.info(f"[ERROR_SEL_FAV-{sender}] для пользователя {sender}: {e}") 
                                            
                    # Ручное добавление в избранное 
                    elif event.obj.message['text'].lower().split(' ')[0] in VkCommands.favList and event.obj.message['text'].lower().find("https://")>=0 and sender in whiteList:
                        store_urls = re.findall(RegexType.regex_store_url_bot, event.obj.message['text'].lower())  
                        items = []
                        for url in store_urls:
                            info = {}
                            info = storeSelector.selectStore(url)
                            info['attachement'] = self._form_images_request_signature([info['mainPhoto']], self.__group_id, tag="custom_fav")[0]
                            info['usr'] = sender

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

    def _get_all_topic_comments(self, group_id, topic_id):

        posts_count = 0
        start_comment_id = 0
        all_posts = []
        try:
            params = {
            'group_id': group_id,
            'topic_id': topic_id,
            'count': 100
            }

            while True:
                params['start_comment_id'] = start_comment_id
                result = self.vk.board.getComments(**params)  
                if result['count'] <= posts_count:
                #if 4 <= posts_count:
                    break
                posts_count += len(result['items'])
                start_comment_id = result['items'][-1]['id']
                all_posts.extend(result['items'].copy())
            return all_posts

        except Exception as e:
            print(e)
            print_exc()          
            return ''
        
    def get_active_url_comment_list(self, group_id, topic_id):

        raw_list = self._get_all_topic_comments(group_id, topic_id)

        new_list = []
        red_flag = False
        
        for item in raw_list:

            urls = re.findall(RegexType.regex_vk_url, item['text'])
            urls.extend(re.findall(RegexType.regex_vk_tag, item['text']))

            if len(urls) == 0:
                continue

            for url in urls:
                url_clean = url.replace('https://vk.com/', '').replace('@', '').replace(')', '')

                try:
                    try:
                        name = f'id{self.get_id(url_clean)}'
                    except:
                        name = f'club{self.get_group_id(url_clean)}'
                    
                    item['text'] = item['text'].replace(url, f'https://vk.com/{name}')
                    
                except Exception as e:
                    print_exc()
                    red_flag = True
                    continue

            if red_flag:
                red_flag = False
                continue   


            # Даты
            if isinstance(item['date'], int):
                item['date'] = datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(item['date'], datetime):
                item['date'] = item['date'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                item['date'] = item['date']

            # Автор
            try:
                name = self.get_name(item['from_id'])    
            except:
                name = self.get_group_name(abs(item['from_id']))
    
            item['from_id'] = name

            new_list.append(item.copy())

        return new_list





#========================
               
    def _get_previous_attachments(self, topic_id: int, comm_id: int) :
        """Получить старые вложения изменяемого комментария

        Args:
            topic_id (int): ID обсуждения
            comm_id (int): ID комментария

        Returns:
            tuple(str, list): Пустая строка или строка, содержащая вложения Вконтакте, разделённые запятыми, и список, содержащий объекты размеров изображений
        """
        result = ''
        result_urls = []
        try:
            comment = self.vk.board.getComments(
                group_id=self.__group_id,
                topic_id=topic_id,
                need_likes=0,
                start_comment_id=comm_id,
                count=1,
                extended=1
            )['items'][0]
            comm_attachments = comment.get('attachments', [])
            for attachment in comm_attachments:
                att_photo = attachment.get('photo', {})
                result += 'photo{}_{},'.format(att_photo.get('owner_id', ''), att_photo.get('id', ''))
                result_urls.append(att_photo['sizes'][-1])
            if result != '':
                if result[len(result) - 1] == ',':
                    result = result[:len(result) - 1:]
            return result, result_urls
        except:
            print_exc()
            return '', []

    def post_comment(self, topic_id: int, message: str, from_group=1, img_urls=[]) -> tuple:
        """Позволяет создать или изменить комментарий в обсуждении. Для изменения нужно передать ссылку на комментарий

        Args:
            topic_name (int): id обсуждения
            message (str): Текст комментария
            from_group (int, optional): От имени кого будет опубликована запись. 1 - от сообщества, 0 - от имени пользователя. По умолч. = 1
            img_urls (list, optional): Список url картинок, которые необходимо прикрепить. По умолчанию = [].

        Returns:
            tuple: Возвращает url созданного / изменённого комментария + список url прикреплённых к нему изображений + словарь topic_id, comment_id
        """
        try:
            params = {
                'group_id': self.__group_id,
                'topic_id': topic_id,
                'message': message,
                'from_group': from_group,
                'guid': random.randint(0, 1000000000),
            }
            attachments = self._form_images_request_signature(img_urls, user= self.__group_id, tag = 'collect', isWallServer= True)

            if attachments != ('', []):
                params.setdefault('attachment', attachments[0])

            comm_id = self.vk.board.createComment(**params)
        
            res_url = 'https://vk.com/topic-{}_{}?post={}'.format(self.__group_id, topic_id, comm_id)
            topic_info = {'topic_id': topic_id, 'comment_id': comm_id}
            return res_url, attachments[1], topic_info
        except:
            print_exc()
            return '', [], {}
        
    def captcha_handler(self, captcha):
        """ При возникновении капчи вызывается эта функция и ей передается объект
            капчи. Через метод get_url можно получить ссылку на изображение.
            Через метод try_again можно попытаться отправить запрос с кодом капчи
        """
        captcha_url = captcha.get_url()

        pprint(captcha_url)
        key = input("Enter captcha code {0}: ".format(captcha_url)).strip()

        # Пробуем снова отправить запрос с капчей
        return captcha.try_again(key)
    
    def find_board_comment(self, topic_id, comment_id):
        """Найти комментарий в обсуждении

        Args:
            topic_id (int): id обсуждения
            comment_id (int): id комментария

        Returns:
            dict: словарь с информацией о комментарии
        """

        params = {
                'group_id': self.__group_id,
                'topic_id': topic_id,
                'count': 1,
                'start_comment_id': comment_id
        }

        return self.vk.board.getComments(**params)['items'][0]

    def edit_collects_activity_comment(self, topic_id, comment_id, status_text = '', 
                                       participant_text = '', 
                                       typeChange = VkTopicCommentChangeType.collect,
                                       img_urls=[]):
        """Изменить комментарий, относящийся к активности коллектов

        Args:
            topic_id (int): id обсуждения
            comment_id (int): id комментария
            status_text (str, optional): текст статуса. Defaults to ''.
            participant_text (str, optional): текст участников. Defaults to ''.
            typeChange (VkTopicCommentChangeType, optional): тип активности. Defaults to VkTopicCommentChangeType.collect.
            img_urls (list, optional): Подгружаемые новые фотографии. Defaults to [].

        Returns:
            int: успешность выполнения. 1 или -1
        """

        comment = self.find_board_comment(topic_id, comment_id)
        old_text = comment['text']
        new_text = ''

        # Изменение статуса
        if status_text:
            if typeChange == VkTopicCommentChangeType.collect:
                status_end_part =  re.search('\n\n\d', old_text).span()[1] - 3
                status_start_part = re.search('Состояние: ', old_text).span()[1]
            elif typeChange == VkTopicCommentChangeType.parcel:
                status_end_part =  re.search('\n\n\w', old_text).span()[1] - 3
                status_start_part = re.search('Статус: ', old_text).span()[1]
            new_text = old_text[:status_start_part] + status_text + old_text[status_end_part:]
        
        # Изменение инфы об оплате
        if participant_text:
            # если статус был уже изменён
            if new_text:
                participants_start_part = re.search('\n\n\d', new_text).span()[1] - 1
                participants_end_part = re.search('\n\nПоедет', new_text).span()[0] + 1
            else:
                participants_start_part = re.search('\n\n\d', old_text).span()[1] - 1
                participants_end_part = re.search('\n\nПоедет', old_text).span()[0] + 1
                new_text = old_text
            new_text = new_text[:participants_start_part] + participant_text + new_text[participants_end_part:]

        attachments = self._get_previous_attachments(topic_id, comment_id)[0]
        if img_urls:
            attachments = ','.join(item for item in [attachments, self._form_images_request_signature(img_urls, user= self.__group_id, tag = 'edit_store', isWallServer= True)[0]] if item)
            
        params_edit = {
            'group_id': self.__group_id,
            'topic_id': topic_id,
            'comment_id': comment_id,
            'message': new_text,
            'attachments': attachments
        }

        try:
            self.vk.board.editComment(**params_edit)
            return 1
        except:
            return -1
        
    def _append_unique_user_id(self, comm: dict, admin_ids: set, user_ids) -> list:
        if comm['from_id'] > 0 and comm['from_id'] not in admin_ids:
            new_id = comm['from_id']
            if new_id not in user_ids:
                user_ids.append(new_id)
        return user_ids
        
    def get_active_comments_users_list(self, post_url: str) -> tuple:
        """Получает список ссылок на страницы пользователей, прокомментировавших пост

        Args:
            post_url (str): Ссылка на пост

        Returns:
            tuple: Возвращает кортеж из списка пользователей и ссылки на пост
        """
        counter = 1
        try:
            post_id = int(post_url[post_url.rfind('_') + 1:])
            admin_ids = set([contact['user_id'] for contact in self.vk.groups.getById(
                    group_ids=self.__group_id, 
                    fields='contacts'
            )[0]['contacts']])
            user_ids = []
            commentators = []
            last_comment_id = -1
            unique_commentators = []
            while (counter == 1 or len(commentators)):
                params = {
                    'owner_id': -int(self.__group_id),
                    'post_id': post_id,
                    'count': 100,
                    'extended': 1,
                    'sort': 'asc',
                    'fields': 'id,first_name,last_name',
                    'thread_items_count': 10
                }
                if counter > 1:
                    params.setdefault('start_comment_id', last_comment_id)
                    params.setdefault('offset', 1)
                vk_response = self.vk.wall.getComments(**params)
                for profile in vk_response.get('profiles', []):
                    if profile not in unique_commentators:
                        unique_commentators.append(profile)
                comments = vk_response.get('items', [])
                counter += 1
                for comm in comments:
                    user_ids = self._append_unique_user_id(comm, admin_ids, user_ids)
                    thread_comments = comm['thread'].get('items', [])
                    if  thread_comments != []:
                        for t_comm in thread_comments:
                            user_ids = self._append_unique_user_id(t_comm, admin_ids, user_ids)
                if comments != []:
                    last_comment_id = comments[-1]['id']
            result = []
            for user_id in user_ids:
                for profile in unique_commentators:
                    if profile['id'] == user_id:
                        new_tuple = 'https://vk.com/id{}'.format(user_id), str(profile['first_name'] + ' ' + profile['last_name'])
                        result.append(new_tuple)
                        unique_commentators.remove(profile)
            return result, post_url
        except:
            print_exc()
            return [], post_url

    def _get_album_cover(self, album_id: int) -> int:
        """
        Args:
            album_id (id): id альбома

        Returns:
            int: ID заглавной фотографии альбома или -1
        """

        try:
            # идентификатор сообщества в параметре owner_id необходимо указывать со знаком "-"
            vk_response = self.vk.photos.getAlbums(owner_id = '-'+self.__group_id, need_covers = 1, album_ids=album_id)
            album = vk_response.get('items', [])
            return album[0]["thumb_id"]
        except Exception as e:
            print_exc()
            return -1


    def delete_photos(self, album_id: int, end_date):
        """Удаляет фото из альбома до указанной даты (не включительно)

        Args:
            album_id (int): id альбома
            end_date (datetime): предельная дата
        """


        cover_id = self._get_album_cover(album_id)

        # идентификатор сообщества в параметре owner_id необходимо указывать со знаком "-"
        params = { "owner_id": '-' + self.__group_id,
                   "album_id": album_id,
                   "extended": 1,
                   "count": 1000
        }

        photos = self.vk.photos.get(**params)

        params_delete = { "owner_id": '-' + self.__group_id,
        }

        for photo in photos["items"]:
            if cover_id != photo["id"]:
                date = (datetime.fromtimestamp(int(photo["date"]))).date()
                if date < end_date:
                    params_delete["photo_id"] = photo["id"]
                    self.vk.photos.delete(**params_delete)
                else:
                    break
