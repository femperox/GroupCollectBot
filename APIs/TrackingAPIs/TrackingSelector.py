from APIs.TrackingAPIs.YandexDeliveryApi import YandexDeliveryApi
from APIs.TrackingAPIs.pochtaApi import PochtaApi
from confings.Consts import TrackingTypes, RegexType

class TrackingSelector():


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
                yandex = YandexDeliveryApi()
                yandex.startDriver()
                item = yandex.getTracking(track)
                yandex.stopDriver()
  
            return item
    