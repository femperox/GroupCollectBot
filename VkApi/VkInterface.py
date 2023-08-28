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
from SQLS.DB_Operations import addFav, getFav, deleteFav, getFandoms, getTags, addBans, insertUpdateParcel
from YahooApi.yahooApi import getAucInfo
from confings.Consts import CURRENT_POSRED, BanActionType, MAX_BAN_REASONS, RegexType, PayloadType
from APIs.utils import getMonitorChats, getFavInfo
from APIs.pochtaApi import getTracking

class VkApi:

    def __init__(self) -> None:
        tmp_dict = json.load(open(os.getcwd()+'/confings/privates.json', encoding='utf-8'))
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
        self.__yahoo = tmp_dict['yahoo_jp_app_id']
        
        vk_session = vk_api.VkApi(token=self.__tok)
        self.__vk_message = vk_session.get_api()
        

        self.lang = 100
    
    def _init_tmp_dir(self) -> None:
        if not os.path.isdir(os.getcwd()+'/tmp'):
            os.mkdir(os.getcwd()+'/tmp')

    def _two_factor_auth(self):
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
                json.dump(privates, open(os.getcwd()+'/confings/privates.json', 'w'))
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

                json.dump(privates, open(os.getcwd()+'/confings/privates.json', 'w'))
                return new_login, new_pass
            new_login = self._encode_decode_str(key, login, encode=False)
            new_pass = self._encode_decode_str(key, password, encode=False)
            return new_login, new_pass
        except:
            print_exc()
            return None, None
        
    def _get_image_extension(self, url):
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
    
    def _vk_image_upload(self, image_name: str, user: str) -> dict:
        """Загружает локальное изображение на сервера Вконтакте

        Args:
            image_name (str): Имя файла с изображением

        Returns:
            dict: В случае успешного выполнения запроса вернёт словарь с представлением медиа Вконтакте
        """
        if image_name != '':
            vk_response = self.vk.photos.getMessagesUploadServer(
                peer_id=user
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

        albums = self.vk.photos.getAlbums(owner_id = f'-{self.__group_id}', need_system=1)

        pprint(self.vk.photos.getAlbumsCount(group_id = self.__group_id))
        
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

    def sendMes(self, mess, users, tag = '', pic = [], type = ''):

        try:          
            
            params = {
                'group_id': self.__group_id,
                'peer_ids': users,
                'message': mess,
                'random_id': 0,
            }


            if type == MessageType.monitor_big_category:
                settings = dict(one_time=False, inline=True)
                keyboard_1 = VkKeyboard(**settings)
                keyboard_1.add_callback_button(label='Забанить продавца', color=VkKeyboardColor.NEGATIVE, payload=PayloadType.ban_seller)
                keyboard_1.add_callback_button(label='Добавить в избранное', color=VkKeyboardColor.POSITIVE, payload=PayloadType.add_fav)

                params['keyboard'] = keyboard_1.get_keyboard()

            if pic != []:
                if pic[0].find('photo')>=0:
                    params.setdefault('attachment', pic[0])
                else:    
                    attachments = self._form_images_request_signature(pic, self.__group_id, tag)
                    if attachments != ('', []):
                        params.setdefault('attachment', attachments[0])

            self.__vk_message.messages.send(**params) 

        except Exception as e:
            print_exc()
    
        
    def get_attachemetns(self, peer_id, conv_id, idx):
        
        params = {
            'group_id': self.__group_id,
            'peer_id': peer_id,
            'conversation_message_ids': conv_id,
        }

        result = self.__vk_message.messages.getByConversationMessageId(**params)
        
        return result['items'][0]['attachments'][idx]['photo']
    
    def monitorChats(self):
       """Мониторинг чатов группы
       """

       banList = ['b', 'ban', 'б', 'бан', r'\ban', r'\b', r'\б', r'\бан']
       favList = ['и', r'\и', '+']
       getFavList = [r'\с', r'\список']
       delFavList = [r'\у', r'\удалить']
       
       hashtagList = ['#инфо', '#избранное']
       
       vkBotSession = vk_api.VkApi(token=self.__tok)
       longPoll = VkBotLongPoll(vkBotSession, self.__group_id)
        
       while True:
        try:
            for event in longPoll.listen():
                #pprint(event)       
                # Исходящие сообщения
                if event.type == VkBotEventType.MESSAGE_REPLY:
                    sender = event. obj['from_id']
                    chat = event.obj['peer_id']
 
                    # Личные сообщение
                    if chat not in getMonitorChats():
                        
                        try:
                            track = re.findall(RegexType.regex_track, event.obj['text'])[0]
                            tracking_info = getTracking(track)
                            tracking_info['rcpnVkId'] = chat

                            insertUpdateParcel(tracking_info)               
                        except:
                            continue   

                # Действия с сообщениями - callback кнопицы        
                elif event.type ==VkBotEventType.MESSAGE_EVENT:

                    chat = event.object['peer_id']
                    message_id = event.object['conversation_message_id']
                    mes = self.get_message(chat_id = chat, mess_id= message_id)

                    if event.object['payload'] == PayloadType.add_fav:

                        item_index = 0
                        fav_item = getFavInfo(mes['items'][0]['text'], item_index)
                        fav_item['usr'] = event.object['user_id']
                        try:
                            fav_item['attachement'] = mes['items'][0]['attachments'][item_index]['photo']
                        except:
                            fav_item['attachement'] = self.get_attachemetns(peer_id=chat, conv_id=message_id, idx = item_index)
                            
                        fav_item['attachement'] = 'photo{}_{}_{}'.format(fav_item['attachement']['owner_id'], fav_item['attachement']['id'], fav_item['attachement']['access_key'])
                        
                        mess = Messages.mes_fav(fav_item = fav_item, fav_func = addFav).format(self.get_name(fav_item['usr']), fav_item['id'])
                        
                        logger_fav.info(f"[ADD_FAV-{sender}] для пользователя {sender}: {mess}")
                        self.sendMes(mess = mess, users = chat)   
                    
                    elif event.object['payload'] == PayloadType.ban_seller and str(event.object['user_id']) in self.__admins:

                        category = re.findall(RegexType.regex_hashtag, mes['items'][0]['text'])

                        seller = category[-1]
                        category = category[0]

                        if seller:
                            path = os.getcwd()+ f'/stopLists/{category.split("_")[-1]}_stop.txt'
                            with open(path, 'a+') as f:
                                f.seek(0)
                                currentStopList = set(f.read().split('\n'))
                                isBanned = seller[1:] in currentStopList

                                message = Messages.mes_ban(seller = seller, category = category, isBanned = isBanned)
                                self.sendMes(mess = message, users= chat)
                                if not isBanned:
                                    f.write(f'\n{seller[1:]}')
                                    logger.info(f"\n[BAN-{category.split('_')[-1]}] Забанен продавец {seller[1:]}\n")                      


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
                                
                    if 'reply_message' in event.obj.message and str(event.obj.message['from_id'])[1:] != self.__group_id:
                       
                        # Добавление в избранное
                        if event.obj.message['text'].lower().split(' ')[0] in favList:
                         
                            try:
                                fav_item = {}
                                sender_text = event.obj.message['text']
                            
                                try: 
                                    item_index = int(sender_text.split(' ')[1])-1 if sender_text.split(' ')[1].isdigit() else 0
                                except:
                                    item_index = 0
                                
                                fav_item['usr'] = sender
                                
                                text = event.obj.message['reply_message']['text']
                                
                                if text.find('#избранное')>=0: 
                                    self.sendMes('В избранное можно добавлять только сообщения с лотами!', chat)
                                    continue

                                fav_item.update(getFavInfo(text, item_index))

                                try:
                                    fav_item['attachement'] = event.obj.message['reply_message']['attachments'][item_index]['photo']
                                except:
                                    fav_item['attachement'] = self.get_attachemetns(peer_id=chat, conv_id=event.obj.message['reply_message']['conversation_message_id'], idx = item_index)
                                    
                                fav_item['attachement'] = 'photo{}_{}_{}'.format(fav_item['attachement']['owner_id'], fav_item['attachement']['id'], fav_item['attachement']['access_key'])
                        
                                mess = Messages.mes_fav(fav_item = fav_item, fav_func = addFav).format(self.get_name(fav_item['usr']), fav_item['id'])
                                
                                logger_fav.info(f"[ADD_FAV-{sender}] для пользователя {sender}: {mess}")
                                self.sendMes(mess, chat)
                            except Exception as e:
                                print(e)                      
                        
                        # Бан продавца
                        if str(sender) in self.__admins and event.obj.message['text'].lower() in banList:
                            try:
                                reply = event.obj.message['reply_message']['text']   
                                
                                # в посте с товаров два тега: тег_категории и тег_продавца
                                category = re.findall(RegexType.regex_hashtag, reply)
                                if hashtagList[0] in category or len(category)==1 or hashtagList[1] in category:
                                    continue
                                seller = category[-1]
                                category = category[0]
                                if seller:
                                    path = os.getcwd()+ f'/stopLists/{category.split("_")[-1]}_stop.txt'
                                    with open(path, 'a+') as f:
                                        f.seek(0)
                                        currentStopList = set(f.read().split('\n'))
                                        isBanned = seller[1:] in currentStopList

                                        message = Messages.mes_ban(seller = seller, category = category, isBanned = isBanned)
                                        self.sendMes(mess = message, users= chat)
                                        if not isBanned:
                                            f.write(f'\n{seller[1:]}')
                                            logger.info(f"\n[BAN-{category.split('_')[-1]}] Забанен продавец {seller[1:]}\n")
                            except:
                                continue
                            
                    elif event.obj.message['text'].lower().split(' ')[0] in getFavList:
                            try:
                                text = event.obj.message['text'].lower()
                                offset = 0
                                if len(text.split(' '))>1 and text.split(' ')[1].isdigit():
                                    offset = int(text.split(' ')[1]) - 1
                                    
                                favListing = getFav(sender, offset)
                                
                                pics = []
                                picStr = ''
                                mess = f'#избранное для {user_name}'
                                if len(favListing[0]) == 0:
                                    mess += f"\n\nВаше избранное пусто для {offset+1} десятки!"
                                else:
                                    for i in range(len(favListing[0])):
                                        picStr += favListing[0][i][2] +','
                                        mess += f'\n\n{i+1}. #{favListing[0][i][1]}\nКонец: {favListing[0][i][-1]}\nПосред: {CURRENT_POSRED.format(favListing[0][i][1])}'
                                    
                                if picStr != '': pics.append(picStr)
                                
                                mess += f'\n\nОтобаржено {len(favListing[0])}/{favListing[1]} лотов в избранном' 
                                
                                logger_fav.info(f"[SEL_FAV-{sender}] для пользователя {sender} выведен список избранного: {','.join([item[1] for item in favListing[0]])}")
                                
                                self.sendMes(mess=mess, users=chat, pic=pics)
                            except Exception as e:
                                pprint(e)
                    
                    # Удаление из избранного
                    elif event.obj.message['text'].lower().split(' ')[0] in delFavList and event.obj.message['text'].lower().find("#")>=0:
                        
                        auc_ids = re.findall(RegexType.regex_hashtag, event.obj.message['text'].lower())
                     
                        mes =  f'#избранное для {user_name}\n' 
                        
                        for id in auc_ids:
                            mes += f"\n{id} удалён из вашего избранного!" if deleteFav(sender, id[1:]) else f"\n{id} и так не значился в вашем избранном!"
                            logger_fav.info(f"[DELETE_FAV-{sender}] для пользователя {sender}: {mes}")
                           
                        self.sendMes(mess=mes, users=chat)
                        
                    # Ручное добавление в избранное 
                    elif event.obj.message['text'].lower().split(' ')[0] in favList and event.obj.message['text'].lower().find("#")>=0:

                        auc_ids = re.findall(RegexType.regex_hashtag, event.obj.message['text'].lower())  
                        
                        try:
                            info = getAucInfo(app_id = self.__yahoo, id= auc_ids[0][1:], tag="custom_fav")
                            info['attachement'] = self._form_images_request_signature([info['pic']], self.__group_id, tag="custom_fav")[0]
                            info['usr'] = sender
                            info['id'] = auc_ids[0][1:]
                            info['date_end'] = info['endTime']
                            
                            mess =  f'#избранное для {user_name}\n'
                            mess += f"\nЛот #{info['id']} был добавлен в ваше избранное!" if addFav(info) else f"\nЛот #{info['id']} уже есть в вашем избранном!"
                        except Exception as e:
                            print(f'Message formatting: {e}')
                            mess += f"\nОшибка добавления лота #{info['id']} в избранное. Попробуйте ещё раз!"
                                
                        logger_fav.info(f"[ADD_FAV-{sender}] для пользователя {sender}: {mess}")
                        self.sendMes(mess, chat)
                        
                        
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



    def post_wall_comment(self, mess, post_id, from_group=1):

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
              
        
    def monitorWall(self):
       """Мониторинг стены группы
       """

       group_tag = '@hideout_collect'
       whiteList = [int(self.__admins[0])]

       vkBotSession = vk_api.VkApi(token=self.__tok)
       longPoll = VkBotLongPoll(vkBotSession, self.__group_id)
    
       while True:
        try:
            for event in longPoll.listen():  
                if event.type == VkBotEventType.WALL_POST_NEW:

                    post = {}
                    post['text'] = event.obj['text']
                    post['id'] = event.obj['id']

                    post['tags'] = re.findall(RegexType.regex_hashtag, post['text'])

                    allFandoms = getFandoms()
                    mess = 'Автотеги.'
                    
                    isTagPost = False
                    
                    for tag in post['tags']:
                        if tag.replace('#','').replace(group_tag, '') in allFandoms:
                            isTagPost = True
                            users = getTags(tag.replace('#','').replace(group_tag, ''))
                            users = '\n'.join([self.get_name(usr) for usr in users])
                            #users = '\n'.join(str(usr) for usr in users)
                            mess += f'\n\n{tag}:\n{users}'
                    
                    if isTagPost:
                        self.post_wall_comment(mess=mess, post_id=post['id'])
                    

                elif  event.type in [VkBotEventType.PHOTO_COMMENT_DELETE, VkBotEventType.WALL_REPLY_DELETE] and event.object['deleter_id'] not in whiteList:
                    
                    deleter_id = event.object['deleter_id'] if event.object['deleter_id'] != 100 else event.object['user_id']

                    count_bans = addBans(deleter_id, BanActionType.deleting.value)

                    if count_bans >= MAX_BAN_REASONS:
                        self.ban_users({'id': deleter_id, 'comment': 'Удаление комментариев.'})

                    mess = f'{self.get_name(deleter_id)}, удаление комментариев запрещено.\n\nПредупреждение {count_bans}/3. На третье будет перманентный бан.'

                    if event.type == VkBotEventType.WALL_REPLY_DELETE:
                        self.post_wall_comment(mess = mess, post_id = event.object['post_id'])
                    else:
                        self.post_photo_comment(mess = mess, photo_id = event.object['photo_id'])
                
                elif  event.type in [VkBotEventType.PHOTO_COMMENT_EDIT, VkBotEventType.WALL_REPLY_EDIT] and event.object['from_id'] not in whiteList:

                    deleter_id = event.object['from_id']

                    count_bans = addBans(deleter_id, BanActionType.editing.value)
                    if count_bans >= MAX_BAN_REASONS:
                        self.ban_users({'id': deleter_id, 'comment': 'Изменение комментариев.'})
                    
                    mess = f'{self.get_name(deleter_id)}, изменение комментариев запрещено.\n\nПредупреждение {count_bans}/3. На третье будет перманентный бан.'

                    if event.type == VkBotEventType.WALL_REPLY_EDIT:
                        self.post_wall_comment(mess = mess, post_id = event.object['post_id'])
                    else:
                        self.post_photo_comment(mess = mess, photo_id = event.object['photo_id'])        

        except Exception as e:
            pprint(e)   
            continue      


