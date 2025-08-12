import requests
from APIs.webUtils import WebUtils
from pprint import pprint
from bs4 import BeautifulSoup
import re
import json
from confings.Consts import PathsConsts, OrdersConsts

class DaromApi:

    class DaromOrderStatus:

        procurement = 'закупка товаров'
        shipped = 'ожидание прихода на склад'
        shipping_soon = 'ожидание отправки продавцом'
        at_warehouse = 'товар на складе'
        cancelled = 'заказ отменен'

        @staticmethod
        def getCollectStatus(status: str):
            """Получить статус заказа в соотвествии с принятыми обозначениями

            Args:
                status (str): статус заказа

            Returns:
                OrdersConsts.OrderStatus: статус заказа общепринятый
            """

            if status in [DaromApi.DaromOrderStatus.procurement, DaromApi.DaromOrderStatus.shipping_soon]:
                return OrdersConsts.OrderStatus.procurement
            elif status in [DaromApi.DaromOrderStatus.shipped]:
                return OrdersConsts.OrderStatus.shipped_JP
            elif status in [DaromApi.DaromOrderStatus.cancelled]:
                return OrdersConsts.OrderStatus.cancelled
            elif status.find(DaromApi.DaromOrderStatus.at_warehouse) >= 0:
                return OrdersConsts.OrderStatus.at_warehouse_JP
            else:
                return OrdersConsts.OrderStatus.empty

    def __init__(self, needAuth = True):

        if needAuth:
            tmp_dict = json.load(open(PathsConsts.PRIVATES_PATH, encoding='utf-8'))
            self.__user = tmp_dict["darom_usr"]
            self.__psw = tmp_dict["darom_psw"]

            session = requests.Session()
            headers = WebUtils.getHeader()
            headers.pop('Content-Type')
            self.headers = headers
            session.headers = self.headers

            # Получаем свежие CSRF и fsig
            auth_url = "https://www.darom.jp/auth"
            response = session.get(auth_url)

            if response.status_code != 200:
                print("Не удалось загрузить страницу авторизации")
                self.session = None
                return

            soup = WebUtils.getSoup(rawText = response.text)
            form = soup.find('form', {'id': 'login_form'})
            
            if not form:
                print("Форма входа не найдена")
                self.session = None
                return

            csrf_token_cookie = session.cookies.get('csrf_token')
            if not csrf_token_cookie:
                print("Cookie csrf_token не установлена")
                self.session = None
                return
            
            csrf_input = form.find('input', {'name': 'csrf'})
            csrf_value = csrf_input['value'] if csrf_input else None

            if not csrf_value:
                print("Не удалось извлечь CSRF токен из формы")
                exit()

            payload = {
                "login": self.__user,
                "password": self.__psw,
                "csrf": csrf_value
            }

            login_response = session.post(
                "https://www.darom.jp/auth",
                data=payload,
                allow_redirects=True
            )

            if "auth" not in login_response.url and "login" not in login_response.url:
                self.session = session
            else:
                self.session = None
        else:
            self.session = None

    def get_num_id(self, id):
        """Получить числовой айди

        Args:
            id (string): id заказа

        Returns:
            int: id заказа
        """

        if isinstance(id, str) and (id.find('P-') >= 0 or id.find('D-') >= 0):
            return int(id.split('-')[-1])
        else:
            return id
        
    def get_darom_order_format(self, id):
        """Получить формат id заказов Дарома

        Args:
            id (string or int): id заказа

        Returns:
            string: id заказа
        """

        return f'D-{id}'

    def get_parcel_orders(self, parcel_id):
        """Получить заказы из посылки

        Args:
            parcel_id (string or int): id посылки

        Returns:
            list[string]: список id
        """

        if self.session:
            url = f'https://www.darom.jp/personal/parcel/details?parcelId={self.get_num_id(id = parcel_id)}'
            response = self.session.get(url)
            soup = WebUtils.getSoup(rawText = response.text)
            soup = soup.find('table', class_ = 'std table-responsive-stack')
            allOrders = soup.findAll('a')
            orderIdsList = []
            for order in allOrders:
                orderIdsList.append(self.get_darom_order_format(order['href'].split('=')[-1]))
            return orderIdsList
        else:
            return []
        
    def get_order_status(self, order_id):
        """Получить статус заказа

        Args:
            order_id (string or int): id заказа

        Returns:
            OrdersConsts.OrderStatus: статус заказа
        """

        if self.session:
            url = f'https://www.darom.jp/personal/orders/details?orderId={self.get_num_id(id = order_id)}'
            response = self.session.get(url)
            soup = WebUtils.getSoup(rawText = response.text)
            soup = soup.find('table').find('td', class_='desktop-size').findAll('span', class_='text')
            return DaromApi.DaromOrderStatus.getCollectStatus(soup[-1].text.split(': ')[-1])

    def get_orders(self, pages = 100):
        """Получить все заказы

        Args:
            pages (int, optional): количество выводимых заказов. Defaults to 100.

        Returns:
            list[dict]: инфо о заказах
        """

        if self.session:

            response = self.session.get(f'https://www.darom.jp/personal/orders?ps={pages}')
            soup = WebUtils.getSoup(rawText = response.text)
            soup = soup.find('div', id = 'orderListByUserFront__10132_list_box')
            allOrders = soup.findAll('tr', class_=['row1', 'row2'])
            ordersInfo = []
            for order in allOrders:
                orderInfo = {}
                orderInfo['id'] = order.find('a').text
                orderInfo['productId'] = order.find('a', class_ = 'highslide')['href'].split('/')[-1].split('-')[0]
                orderInfo['status'] = order.findAll('td')[-1].text
                if orderInfo['status'].find('P-') >= 0:
                    orderInfo['parcelId'] = orderInfo['status']
                    orderInfo['status'] = OrdersConsts.OrderStatus.shipped_transit
                else:
                    orderInfo['status'] = DaromApi.DaromOrderStatus.getCollectStatus(status = orderInfo['status'])
                ordersInfo.append(orderInfo.copy())

            return ordersInfo
        else:
            return []


    def get_active_orders(self):
        """Получить все активные заказы

        Returns:
            list[dict]: инфо о заказах
        """

        orders = self.get_orders()
        return {order['id']: order for order in orders if order['status'] not in [OrdersConsts.OrderStatus.cancelled, OrdersConsts.OrderStatus.shipped_transit]}