from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from confings.Consts import VK_AUTOTAG_FORM_URL, PayloadType, PayloadPriceCheckCountry
from confings.Messages import MessageType

class VkButtons:

    @staticmethod
    def form_back_button(payload):

        settings = dict(one_time = False, inline=True)
            
        keyboard = ''

        keyboard = VkKeyboard(**settings)

        keyboard.add_callback_button(label='⏪ Назад', color=VkKeyboardColor.SECONDARY, payload = payload) 

        return keyboard

    @staticmethod
    def form_menu_buttons(isAddButton = False, buttonPayloadText = ''):
        """Подготовить кнопки для меню

        Args:
            isAddButton (bool, optional): флаг кнопки выкупа. Defaults to False.
            buttonPayloadText (str, optional): текст для пейлода. Defaults to ''.

        Returns:
            VkKeyboard: кнопки меню
        """

        settings = dict(one_time = False, inline=True)
            
        keyboard = ''

        keyboard = VkKeyboard(**settings)

        if isAddButton:
            keyboard.add_callback_button(label='🔖 Поставить на выкуп', color=VkKeyboardColor.POSITIVE, payload= {"type": PayloadType.menu_bot_add_item["type"],  "text": buttonPayloadText}) 

        else:
            keyboard.add_openlink_button(link = VK_AUTOTAG_FORM_URL, label ='📩 Добавиться к автотегам')
            keyboard.add_line()
            keyboard.add_callback_button(label='📦 Мои позиции', color=VkKeyboardColor.SECONDARY, payload= PayloadType.menu_bot_get_orders)
            keyboard.add_line()
            keyboard.add_callback_button(label='🛒 Узнать цену товара (🇯🇵)', color=VkKeyboardColor.PRIMARY, payload= PayloadType.menu_check_price)
            keyboard.add_line()
            keyboard.add_callback_button(label='🛒 Узнать цену товара (🇺🇸)', color=VkKeyboardColor.PRIMARY, payload= {"type": PayloadType.menu_check_price["type"], "country": PayloadPriceCheckCountry.us } )
        return keyboard
    
    @staticmethod
    def form_menu_buying_buttons(userId, userMesId):
        """Подготовить кнопки для меню выкупа

        Returns:
            VkKeyboard: кнопки меню выкупа
        """
        
        settings = dict(one_time= False, inline=True)
            
        keyboard = VkKeyboard(**settings)

        keyboard.add_callback_button(label ='Добавить в ⭐️', color=VkKeyboardColor.SECONDARY, payload= PayloadType.buy_fav)
        keyboard.add_line()

        keyboard.add_callback_button(label='Товар выкуплен', color=VkKeyboardColor.POSITIVE, payload= {"type": PayloadType.buy_succes["type"],  "user": userId, "userMes": userMesId})
        keyboard.add_callback_button(label='Товар НЕ выкуплен', color=VkKeyboardColor.NEGATIVE, payload= {"type": PayloadType.buy_fail["type"],  "user": userId, "userMes": userMesId})

        return keyboard

    @staticmethod
    def form_inline_buttons(type, items = []):
        """_summary_

        Args:
            type (MessageType): тип подборки
            items (list, optional): список товаров подборки. Defaults to [].

        Returns:
            VkKeyboard: кнопки для подборок товаров
        """

        settings = dict(one_time=False, inline=True)
        
        keyboard = ''

        if type == MessageType.monitor_big_category:  
                    
            keyboard = VkKeyboard(**settings)
            keyboard.add_callback_button(label='🚫', color=VkKeyboardColor.NEGATIVE, payload=PayloadType.ban_seller)
            keyboard.add_callback_button(label='⭐️', color=VkKeyboardColor.POSITIVE, payload=PayloadType.add_fav)
        
        elif type in [MessageType.monitor_big_category_other, MessageType.monitor_seller, MessageType.fav_list]:

            keyboard = VkKeyboard(**settings)
            j = 0
            columnn_count = 5
            for i in range(len(items)):
                
                if j % columnn_count == 0 and j!=0:
                    keyboard.add_line()

                if type in [MessageType.monitor_big_category_other, MessageType.monitor_seller]:
                    payload = {"type": PayloadType.add_fav_num["type"], "text": PayloadType.add_fav_num["text"].format(i)}
                    keyboard.add_callback_button(label=f'⭐️ {i+1}', color=VkKeyboardColor.POSITIVE, payload=payload)
                
                elif type in [MessageType.fav_list]:
                    payload = {"type": PayloadType.delete_fav_num["type"], "text": PayloadType.delete_fav_num["text"].format(i)}
                    keyboard.add_callback_button(label=f'🗑 {i+1}', color=VkKeyboardColor.SECONDARY, payload=payload)

                j += 1

        # для чего?
        if type in [MessageType.monitor_big_category_other]:
            j = 0
            columnn_count = 5
            for i in range(len(items)):
                
                if j % columnn_count == 0:
                    keyboard.add_line()

                payload = {"type": PayloadType.ban_seller_num["type"], "text": PayloadType.ban_seller_num["text"].format(i)}
                keyboard.add_callback_button(label=f'🚫 {i+1}', color=VkKeyboardColor.NEGATIVE, payload=payload)
                
                j += 1

        return keyboard