import requests
from APIs.webUtils import WebUtils
import json
from confings.Consts import PathsConsts, OrdersConsts
import certifi

class EasyShipApi:

    payload_orders = 'Incoming'
    payload_parcels = ''

    class EasyShipOrderStatus:

        packing = 26
        procurement = 1
        shipped_admin = 15

        @staticmethod
        def getCollectStatus(status: int):
            """Получить статус заказа в соотвествии с принятыми обозначениями

            Args:
                status (int): статус заказа

            Returns:
                OrdersConsts.OrderStatus: статус заказа общепринятый
            """

            if status in [EasyShipApi.EasyShipOrderStatus.packing]:
                return OrdersConsts.OrderStatus.packing
            elif status in [EasyShipApi.EasyShipOrderStatus.procurement]:
                return OrdersConsts.OrderStatus.procurement
            elif status in [EasyShipApi.EasyShipOrderStatus.shipped_admin]:
                return OrdersConsts.OrderStatus.shipped_admin
            else:
                return OrdersConsts.OrderStatus.empty

    def __init__(self):
            
            tmp_dict = json.load(open(PathsConsts.PRIVATES_PATH, encoding='utf-8'))
            self.__user = tmp_dict["es_usr"]
            self.__psw = tmp_dict["es_psw"]

            auth_url = 'https://lk.easyship.ru/api/login'

            session = requests.Session()
            headers = WebUtils.getHeader()
            headers.pop('Content-Type')
            session.headers = headers

            payload = {
                "email": self.__user,
                "password": self.__psw,
            }

            login_response = session.post(
                auth_url,
                json=payload,
                verify=certifi.where() 
            )

            if login_response.json()['status'] == 'donelogged':
                self.session = session
            else:
                self.session = None

    def get_num_id(self, id):
        """Получить числовой айди

        Args:
            id (string): id заказа

        Returns:
            int: id заказа
        """

        if isinstance(id, str) and (id.find('o') >= 0 or id.find('s') >= 0):
            return int(id[1:])
        else:
            return id

    def get_good_item_documents(self, payload = None):
        """Исполнить метод апи

        Args:
            payload (string): определение payload

        Returns:
            json: json инфо
        """
         
        if self.session:
            url = 'https://lk.easyship.ru/api/getGoodItemDocuments'
            payload_dict = {}
            if payload:
                payload_dict = {"inOutFilter": payload}
            if payload_dict:
                response = self.session.post(url = url, json = payload_dict)
                return response.json()
            else:
                return {}
        else:
            return {}
        
    def get_good_item_document(self, parcel_id = -1):
            """Исполнить метод апи getGoodItemDocument - для единичных айтемо

            Args:
                parcel_id (int): id посылки

            Returns:
                json: json инфо
            """
            
            if self.session:
                url = 'https://lk.easyship.ru/api/getGoodItemDocument'
                payload_dict = {}
                if self.get_num_id(id = parcel_id) > 0:
                    payload_dict = {"xEntity":{"id": self.get_num_id(id = parcel_id), 
                                            "table": "x_orders",
                                            "value": {}}}
                if payload_dict:
                    response = self.session.post(url = url, json = payload_dict)
                    return response.json()
                else:
                    return {}
            else:
                return {}
        

    def get_order_format(self, id):
        """Получить формат id заказов es

        Args:
            id (string or int): id заказа

        Returns:
            string: id заказа
        """

        return f's{id}'

    def get_orders(self):
        """Получить все заказы

        Returns:
            list[dict]: инфо о заказах
        """
        
        orders = self.get_good_item_documents(payload = EasyShipApi.payload_orders)
        if not orders:
            return []
        orders_info = []
        for order in orders['documents']:

            # у себя в кабинете помечаю те что уже сдулись так
            if order['title'].lower().find('delete') >= 0:
                continue

            order_info = {}
            order_info['posred_id'] = self.get_order_format(id = order['uid'])
            order_info['tracking_id'] = order['track_number']
            order_info['title'] = order['title']
            order_info['product_id'] = ''
            
            order_info['status'] = EasyShipApi.EasyShipOrderStatus.getCollectStatus(order['status'])
            orders_info.append(order_info.copy())

        return orders_info
    
    def get_parcel_orders(self, parcel_id):
            """Получить заказы из посылки

            Args:
                parcel_id (string or int): id посылки

            Returns:
                list[string]: список id
            """

            orders = self.get_good_item_document(parcel_id = parcel_id)
            if not orders:
                return []
            order_ids_list = []
            for order in orders['document']['included_documents']:
                order_ids_list.append(self.get_order_format(id = order['uid']))
            return order_ids_list
    
    def get_active_orders(self):
            """Получить все активные заказы

            Returns:
                list[dict]: инфо о заказах
            """

            orders = self.get_orders()
            return {order['posred_id']: order for order in orders if order['status'] not in [OrdersConsts.OrderStatus.packing]}