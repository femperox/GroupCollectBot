from confings.Consts import VkCoverSize
import random

class VkParams:

    @staticmethod
    def getSendMessageEventAnswerParams(user_id, peer_id, event_id):
        """Подготовить параметры для отправки события с действием, которое произойдет при нажатии на callback-кнопку

        Args:
            user_id (int): id пользователя
            peer_id (int): id диалога со стороны сообщества
            event_id (string): id события

        Returns:
            dict: параметры для отправки события с действием, которое произойдет при нажатии на callback-кнопку
        """

        params = {
            'user_id': user_id,
            'peer_id': peer_id,
            'event_id': event_id,              
        }   
    
        return params

    @staticmethod
    def getSendMessageParams(group_id, peer_ids, message, reply_to = 0, attachment = '', keyboard = ''):
        """Подготовить параметры для отправки сообщения

        Args:
            group_id (int): id группы
            peer_ids (list of string): id получателей сообщения
            message (string): Текст сообщения
            reply_to (int, optional): id сообщения, на которое требуется ответить. Defaults to 0.
            attachment (str, optional): Объект или несколько объектов, приложенных к записи. Defaults to ''.
            keyboard (str|Keyboard, optional): Объект, описывающий клавиатуру бота. Defaults to ''.

        Returns:
            dict: параметры для отправки сообщения
        """

        params = {
                'group_id': group_id,
                'peer_ids': peer_ids,
                'message': message,
                'random_id': 0,
                'reply_to': reply_to
            }
        
        if reply_to:
            params['reply_to'] = reply_to
        if attachment:
            params['attachment'] = attachment
        if keyboard:
            params['keyboard'] = keyboard

        return params

    @staticmethod
    def getEditMessageParams(peer_id, message, group_id, conversation_message_id, attachment = ''):
        """Подготовить параметры для изменения сообщения

        Args:
            peer_id (int): id беседы
            message (string): новый текст изменяемого сообщения
            group_id (int): id группы
            conversation_message_ids (int): id сообщения в беседе
            attachment (string): Объект или несколько объектов, приложенных к записи

        Returns:
            dict: параметры для изменения сообщения
        """

        params = {
            'peer_id' : peer_id,
            'message': message,
            'group_id': group_id,
            'conversation_message_id': conversation_message_id,
            'keyboard': '',
        }

        if attachment:
            params['attachment'] = attachment

        return params

    @staticmethod
    def getDeleteMessageParams(peer_id, group_id, cmids, delete_for_all = 1):
        """Подготовить параметры для удаления сообщения

        Args:
            peer_id (int): id беседы
            group_id (int): id группы
            cmids (int): id сообщения в беседе
            delete_for_all (int, optional): флаг удаления для всех. Defaults to 1.

        Returns:
            dict: параметры для удаления сообщения
        """

        params = {
                    'peer_id' : peer_id,
                    'group_id': group_id,
                    'cmids': cmids,
                    'delete_for_all': delete_for_all,
                }
        
        return params
    
    @staticmethod
    def getConversationMessageIdParams(peer_id, group_id, conversation_message_ids):
        """Получить параметры для информации об сообщении

        Args:
            peer_id (int): id беседы
            group_id (int): id группы
            conversation_message_ids (int): id сообщения в беседе

        Returns:
            dict: параметры для информации об сообщении
        """

        params = {
                    'group_id': group_id,
                    'peer_id': peer_id,
                    'conversation_message_ids': conversation_message_ids,
                }
        
        return params
    
    @staticmethod
    def getSetStatusParams(group_id, text):
        """Подготовить параметры для смены статуса сообщества

        Args:
            group_id (int): id группы
            text (string): новый текст статуса

        Returns:
            dict: параметры для смены статуса сообщества
        """

        params = {
                'group_id': group_id,
                'text': text,
        }

        return params
    
    @staticmethod
    def getOwnerCoverPhotoUploadServerParams(group_id):
        """Получить параметры для подготовки загрузки шапки сообщества

        Args:
            group_id (int): id группы

        Returns:
            dict: параметры для подготовки загрузки шапки сообщества
        """
        
        params = {
                    'group_id': group_id,
                    'crop_x': VkCoverSize.crop_x,
                    'crop_y': VkCoverSize.crop_y,
                    'crop_x2': VkCoverSize.crop_x2,
                    'crop_y2': VkCoverSize.crop_y2
                }
        
        return params 

    @staticmethod
    def getPhotosSaveParams(photo, hash, group_id = 0, server = 0):
        """Подготовить параметры для сохранения фотографии в Вк

        Args:
            photo (string): Фотография в формате multipart/form-data
            hash (string): Хеш фотографий
            group_id (int, optional): id группы. Defaults to 0.
            server (int, optional): id сервера, на который загружены фотографии.. Defaults to 0.

        Returns:
            dict: параметры для сохранения фотографии в Вк
        """
        
        params = {
                    'photo': photo,
                    'hash': hash,
                }
        
        if group_id:
            params['group_id'] = group_id
        if server:
            params['server'] = server
        
        return params
    
    @staticmethod
    def getPhotoCreateCommentParams(owner_id, photo_id, message, from_group = 1):
        """Подготовить параметры для размещения комментария под фотографией

        Args:
            owner_id (int): id пользователя или сообщества, являющегося хозяином фотографии
            photo_id (int): id фотографии
            message (string): текст сообщения
            from_group (int, optional): флаг размещения коммента от лица группы. Defaults to 0.

        Returns:
            dict: параметры для размещения комментария под постом
        """
        
        params = {
                'owner_id': owner_id,
                'photo_id': photo_id,
                'message': message,
                'from_group': from_group,
                'guid': 0,
        }
        
        return params
    
    @staticmethod
    def getPhotoGetParams(owner_id, album_id, extended = 0, count = 1000):
        """Подготовить параметры для получения фотографий из альбома

        Args:
            owner_id (int): id пользователя или сообщества, являющегося хозяином альбома
            album_id (int): id альбома
            extended (int, optional): флаг дополнительных полей. Defaults to 0.
            count (int, optional): количество сообщений, которое необходимо получить. Defaults to 1000.

        Returns:
            dict: параметры для получения фотографий из альбома
        """

        params = { 
                'owner_id': owner_id,
                'album_id': album_id,
                'extended': extended,
                'count': count
        }

        return params

    @staticmethod
    def getPhotoDeleteParams(owner_id, photo_id):
        """Подготовить параметры для удаления фотографии

        Args:
            owner_id (int): id пользователя или сообщества, являющегося хозяином фотографии
            photo_id (int): id фотографии

        Returns:
            dict: параметры для удаления фотографии
        """

        params = { 
                'owner_id': owner_id,
                'photo_id': photo_id
        }

        return params     
    
    @staticmethod
    def getAlbumsParams(owner_id, need_system = 0, need_covers = 0, album_ids = 0):
        """Подготовить параметры для получения инфы об альбоме

        Args:
            owner_id (string): id пользователя или сообщества, которому принадлежат альбомы
            need_system (int, optional): флаг выгрузки системных альбомов, имеющих отрицательные идентификаторы. Defaults to 0.
            need_covers (int, optional): флаг выгрузки адреса изображения-обложки. Defaults to 0.
            album_ids (int, optional): id альбома. Defaults to 0.

        Returns:
            dict: параметры для получения инфы об альбоме
        """

        params = {
                    'owner_id': owner_id,
                    'need_system': need_system,
                    'need_covers': need_covers
                }
        
        if album_ids != 0:
            params['album_ids'] = album_ids 

        return params
    
    @staticmethod
    def getUsersParams(user_ids, lang):
        """Подготовить параметры для получения инфы о пользоваателе

        Args:
            user_ids (int): id пользователя
            lang (int): id языка

        Returns:
            dict: параметры для получения инфы о пользоваателе
        """
        
        params = {
                    'user_ids': user_ids,
                    'lang': lang,
                }
        
        return params

    @staticmethod
    def getGroupsParams(group_id, lang):
        """Подготовить параметры для получения инфы о сообществе

        Args:
            group_id (int): id сообщества
            lang (int): id языка

        Returns:
            dict: параметры для получения инфы о сообществе
        """
        
        params = {
                    'group_id': group_id,
                    'lang': lang,
                }
        
        return params    

    @staticmethod
    def getRemoveChatUserParams(chat_id, user, member_id):
        """Подготовить параметры для удаления пользователя из конфы

        Args:
            chat_id (int): id конфы
            user (int): id пользователя, которого необходимо исключить из беседы
            member_id (int): id участника, которого необходимо исключить из беседы. Для сообществ — идентификатор сообщества со знаком «минус»

        Returns:
            dict: параметры для удаления пользователя из конфы
        """

        params = {
                    'chat_id': chat_id,
                    'user': user,
                    'member_id': member_id
                }
        
        return params  
    
    @staticmethod
    def getGroupBanParams(group_id, owner_id, comment):
        """Подготовить параметры для бана в сообществе

        Args:
            group_id (int): id группы
            owner_id (int): id пользователя, которого нужно забанить
            comment (string): текст бана

        Returns:
            dict: параметры для бана в сообществе
        """
        
        params = {
                'group_id': group_id,
                'comment_visible': 1,
                'owner_id': owner_id,
                'comment': comment
        }

        return params

    @staticmethod
    def getIsMemberParams(group_id, user_id):
        """Подготовить параметры для запроса принадлежности к сообществу

        Args:
            group_id (int): id сообщества
            user_id (int): id пользователя

        Returns:
            dict: параметры для запроса принадлежности к сообществу
        """

        params = {
                    'group_id': group_id,
                    'user_id': user_id,
                }
        
        return params 
    
    @staticmethod
    def getWallCreateCommentParams(owner_id, post_id, message, from_group = 1):
        """Подготовить параметры для размещения комментария под постом

        Args:
            owner_id (int): id пользователя или сообщества, на стене которого находится запись
            post_id (int): id записи на стене
            message (string): текст сообщения
            from_group (int, optional): флаг размещения коммента от лица группы. Defaults to 1.

        Returns:
            dict: параметры для размещения комментария под постом
        """
        
        params = {
                'owner_id': owner_id,
                'post_id': post_id,
                'message': message,
                'from_group': from_group,
                'guid': 0,
        }
        
        return params
    
    @staticmethod
    def getWallGetParams(owner_id, filter = 'postponed'):
        """Подготовить параметры для получения записей со стены

        Args:
            owner_id (int): id пользователя или сообщества, на стене которого находится запись
            filter (str, optional): фильтр типа искомых записей. Defaults to 'postponed'.

        Returns:
            dict: параметры для получения записей со стены
        """

        params = {
                'owner_id': owner_id,
                'filter': filter
        }
        
        return params

    @staticmethod
    def getWallGetCommentsParams(owner_id, post_id, start_comment_id = 0, count = 100, extended = 0, offset = 1):
        """Подготовить параметры для получения информации о комментарии под записью

        Args:
            owner_id (int): id пользователя или сообщества, на стене которого находится запись
            post_id (int): id записи на стене
            start_comment_id (int, optional): id комментария, начиная с которого нужно вернуть список. Defaults to 0.
            count (int, optional): число комментариев, которые необходимо получить. Defaults to 100.
            extended (int, optional): флаг дополнительных полей. Defaults to 0.
            offset (int, optional): сдвиг, необходимый для получения конкретной выборки результатов. Defaults to 1.

        Returns:
            dict: параметры для получения информации о комментарии под записью
        """

        params = {
                'owner_id': owner_id,
                'post_id': post_id,
                'start_comment_id': start_comment_id,
                'count': count,
                'extended': extended,
                'sort': 'asc',
                'fields': 'id,first_name,last_name',
                'thread_items_count': 10,
                'offset': offset
        }

        return params

    @staticmethod
    def getWallEditPostParams(owner_id, post_id, message):
        """Подготовить параметры для изменения записи на стене

        Args:
            owner_id (int): id пользователя или сообщества, на стене которого находится запись
            post_id (int): id записи на стене
            message (string): текст сообщения

        Returns:
            dict: параметры для изменения записи на стене
        """
        
        params = {
                'owner_id': owner_id,
                'post_id': post_id,
                'message': message
        }   

        return params
    
    @staticmethod
    def getBoardGetComments(group_id, topic_id, start_comment_id = -1, count = 100, need_likes = 0, extended = 0):
        """Подготовить параметры для поиска комментариев в обсуждении

        Args:
            group_id (int): id сообщества
            topic_id (int): id обсуждения
            start_comment_id (int, optional): id комментария, начиная с которого нужно вернуть список. Defaults to -1.
            count (int, optional): количество сообщений, которое необходимо получить. Defaults to 100.
            need_likes(int, optional): флаг дополнительного поля likes. Defaults to 0.
            extended(int, optional): флаг расширенной информации о комментарии. Defaults to 0.

        Returns:
            dict: параметры для поиска комментариев в обсуждении
        """
        
        params = {
                'group_id': group_id,
                'topic_id': topic_id,
                'count': count,
                'need_likes': need_likes,
                'extended': extended
        }

        if start_comment_id > -1:
            params['start_comment_id'] = start_comment_id

        return params
    
    @staticmethod
    def getBoardCreateComment(group_id, topic_id, message, from_group = 1, attachment = ''):
        """Подготовить параметры для размещения комментария в обсуждении

        Args:
            group_id (int): id сообщества
            topic_id (int): id обсуждения
            message (string): текст комментария
            from_group (int, optional): флаг размещения коммента от лица группы. Defaults to 1.
            attachment (str, optional): Объект или несколько объектов, приложенных к записи. Defaults to ''.

        Returns:
            dict: параметры для размещения комментария в обсуждении
        """

        params = {
                'group_id': group_id,
                'topic_id': topic_id,
                'message': message,
                'from_group': from_group,
                'guid': random.randint(0, 1000000000),
        }

        if attachment:
            params['attachment'] = attachment
        
        return params
    
    @staticmethod
    def getBoardEditComment(group_id, topic_id, comment_id, message = '', attachments = ''):
        """Подготовить параметры для изменения комментария в обсуждении

        Args:
            group_id (int): id сообщества
            topic_id (int): id обсуждения
            comment_id (int): id комментария, который нужно изменить
            message (str, optional): текст комментария. Defaults to ''.
            attachments (str, optional): Объект или несколько объектов, приложенных к записи. Defaults to ''.

        Returns:
            dict: параметры для изменения комментария в обсуждении
        """

        params = {
                'group_id': group_id,
                'topic_id': topic_id,
                'comment_id': comment_id,
        }

        if message:
            params['message'] = message
        if attachments:
            params['attachments'] = attachments     

        return params


