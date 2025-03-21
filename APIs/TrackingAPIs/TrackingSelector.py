from APIs.TrackingAPIs.YandexDeliveryApi import YandexDeliveryApi
from APIs.TrackingAPIs.pochtaApi import PochtaApi
from APIs.TrackingAPIs.cdekApi import CdekApi
from confings.Consts import RegexType

class TrackingTypes():
     ids = {RegexType.regex_track : 'pochta_RF',
            RegexType.regex_track_yandex: 'yandex_delivery',
            RegexType.regex_track_cdek: 'cdek'
            }

class TrackingSelector():

    def selectArrivedStatuses(type):
        """определяет значение статуса "доставлено" для каждого типа доставки

        Args:
            type (string): тип доставки

        Returns:
            array of string: статусы
        """
         
        if type == TrackingTypes.ids[RegexType.regex_track_cdek]:
            return [CdekApi.arrived_status]
        elif type == TrackingTypes.ids[RegexType.regex_track_yandex]:
            return [YandexDeliveryApi.arrived_status]
        elif type == TrackingTypes.ids[RegexType.regex_track]:
            return [PochtaApi.arrived_status, PochtaApi.notice_arrived_status]
        

    def selectTracker(track, type):
            
            """Определение службы доставки по типу и получение данных по треку

            Args:
                track (string): трекинг посылки
                type (string): тип доставки
                stopDriver (boolean): остановить драйвер для Яндекс доставки

            Returns:
                dict: информация о трекинге по заданному треку
            """

            item = {}
            if type == TrackingTypes.ids[RegexType.regex_track]:
                item = PochtaApi.getTracking(track)

            elif type == TrackingTypes.ids[RegexType.regex_track_yandex]:
                item = YandexDeliveryApi.getTrackingByApi(track)
            
            elif type == TrackingTypes.ids[RegexType.regex_track_cdek]:
                 cdek = CdekApi()
                 cdek.startDriver()
                 item = cdek.getTracking(track)
                 cdek.stopDriver()
  
            return item
    