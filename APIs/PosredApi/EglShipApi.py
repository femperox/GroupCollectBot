import json 
import requests
from confings.Consts import PathsConsts, OrdersConsts
from APIs.webUtils import WebUtils
from APIs.PosredApi.PosredOrderInfoClass import PosredOrderInfoClass
from typing import List

class EglShipApi:

    class EglShipOrderStatus:

        draft = 'draft'
        procurement = 'expecting'
        at_warehouse = 'toSend'

        @staticmethod
        def getCollectStatus(status: str):
            """Получить статус заказа в соотвествии с принятыми обозначениями

            Args:
                status (str): статус заказа

            Returns:
                OrdersConsts.OrderStatus: статус заказа общепринятый
            """

            if status in [EglShipApi.EglShipOrderStatus.procurement]:
                return OrdersConsts.OrderStatus.procurement
            elif status in [EglShipApi.EglShipOrderStatus.at_warehouse]:
                return OrdersConsts.OrderStatus.at_warehouse_US
            else:
                return OrdersConsts.OrderStatus.empty

    def __init__(self):
            
            tmp_dict = json.load(open(PathsConsts.PRIVATES_PATH, encoding='utf-8'))
            self.__user = tmp_dict['egl_usr']
            self.__psw = tmp_dict['egl_psw']

            auth_url = 'https://eglship.us/api/pa/auth'

            session = requests.Session()
            headers = WebUtils.getHeader()
            headers.pop('Content-Type', None) 
            session.headers.update(headers)

            session.get('https://eglship.us/login')
            xsrf_from_cookie = session.cookies.get('XSRF-TOKEN')

            if not xsrf_from_cookie:
                self.session = None
                raise Exception("Не удалось получить XSRF-TOKEN")

            session.headers['X-XSRF-TOKEN'] = xsrf_from_cookie
            session.headers["Referer"] = "https://eglship.us/lk"
            session.headers["X-KL-saas-Ajax-Request"] = "Ajax_Request"
            session.headers["Sec-Fetch-Dest"] = "empty"
            session.headers["Sec-Fetch-Mode"] = "cors"
            session.headers["Sec-Fetch-Site"] = "same-origin"

            payload = {
                "phone": self.__user,
                "password": self.__psw,
            }

            login_response = session.post(
                auth_url,
                json=payload, 
            )

            if login_response.json()['success']:
                self.session = session
            else:
                self.session = None

    def get_profile_info(self):
        """Получить информацию о профиле

        Returns:
            dict: словарь с информацией о профиле
        """
        
        if not self.session:
            print('Сессия пуста')
            return {}
        
        curl = 'https://eglship.us/api/pa/profile'

        response = self.session.get(curl)
        return response.json()
    
    def get_orders(self, limit = 100) -> List[PosredOrderInfoClass]:
        """Получить все заказы

        Returns:
            list[dict]: инфо о заказах
        """
        
        if not self.session:
            print('Сессия пуста')
            return []
        curl = 'https://eglship.us/api/pa/incoming-list'

        payload = {
            "per-page": limit,
        }
        response = self.session.get(curl, params=payload)
        orders = response.json()

        if not orders:
            return []
        orders_info = []
        for order in orders['data']:

            # у себя в кабинете помечаю те что уже сдулись так
            if order['name'].lower().find('delete') >= 0:
                continue

            order_info = {}
            order_info['posred_id'] = order['id']
            order_info['tracking_id'] = order['trackNumber']
            order_info['title'] = order['name']
            order_info['product_id'] = order['orderNumber']
            
            order_info['status'] = EglShipApi.EglShipOrderStatus.getCollectStatus(order['status'])
            orders_info.append(PosredOrderInfoClass(**order_info.copy()))

        return orders_info
    
    def get_active_orders(self):
        """Получить все активные заказы

        Returns:
            list[dict]: инфо о заказах
        """

        orders = self.get_orders()
        return {order.posred_id: order for order in orders if order.status not in [OrdersConsts.OrderStatus.packing]}