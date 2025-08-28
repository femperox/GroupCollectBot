from confings.Consts import OrdersConsts
from _utils.dateUtils import DateUtils
from confings.Consts import RegexType

class TrackingTypes():
    ids = {RegexType.regex_track : 'pochta_RF',
            RegexType.regex_track_yandex: 'yandex_delivery',
            RegexType.regex_track_cdek: 'cdek'
            }
     

class TrackInfoClass:

    def __init__(self, barcode = '', sndr = '', rcpn = '', destinationIndex = '',
                    operationIndex = '', operationDate = None, operationType = '',
                    operationAttr = '', mass = 0, rcpnVkId = -1, trackingType = TrackingTypes.ids[RegexType.regex_track], 
                    notified = 0, **kwargs):
            
            self.barcode = barcode
            self.sndr = sndr
            self.rcpn = rcpn
            self.destinationIndex = destinationIndex
            self.operationIndex = operationIndex
            self.operationDate = operationDate
            self.operationType = operationType
            self.operationAttr = operationAttr
            self.mass = mass
            self.rcpnVkId = rcpnVkId
            self.trackingType = trackingType
            self.notified = notified

    def __bool__(self):
        return bool(self.barcode) and bool(self.destinationIndex)

    def __repr__(self):
        formatted_string = "\n".join([f"'{attr}': {value}," for attr, value in vars(self).items()])
        return f"TrackInfoClass(\n{formatted_string})"
    
    def setRcpnVkId(self, rcpnVkId):
        self.rcpnVkId = rcpnVkId

    def setTrackingTypeByKey(self, trackingTypeKey: RegexType):
        self.trackingType = TrackingTypes.ids[trackingTypeKey]
    
    def setTrackingType(self, trackingType):
        self.trackingType = trackingType

    def setNotified(self, notified):
        self.notified = notified