from confings.Consts import OrdersConsts
from _utils.dateUtils import DateUtils

class ProductInfoClass:

    def __init__(self, id = '', itemPrice = 0, tax = 0, itemPriceWTax = 0,
                shipmentPrice = OrdersConsts.ShipmentPriceType.undefined, page = '', mainPhoto = '',
                name = '', endTime = None, siteName = '', posredCommission = 0, posredCommissionValue = 0,
                isMembershipNeeded:bool = False, blitz = -1, seller = '', goodRate = -1, badRate = -1,
                releaseDate = None, priceForFreeShipment = -1, country = OrdersConsts.OrderTypes.empty, 
                status = OrdersConsts.StoreStatus.undefined, **kwargs):
        
        self.id = id
        self.itemPrice = itemPrice
        self.tax = tax
        self.itemPriceWTax = itemPriceWTax
        self.shipmentPrice = shipmentPrice
        self.page = page
        self.mainPhoto = mainPhoto
        self.name = name
        self.endTime = endTime if endTime else DateUtils.getDefaultEndTimeForProduct()
        self.siteName = siteName
        self.posredCommission = posredCommission
        self.posredCommissionValue = posredCommissionValue
        self.isMembershipNeeded = isMembershipNeeded
        self.blitz = blitz
        self.attachement = None
        self.user = None
        self.seller = seller 
        self.goodRate = goodRate 
        self.badRate = badRate
        self.releaseDate = releaseDate
        self.priceForFreeShipment = priceForFreeShipment
        self.country = country
        self.status = status

    def __bool__(self):
        return bool(self.id) and bool(self.siteName)

    def __repr__(self):
        formatted_string = "\n".join([f"'{attr}': {value}," for attr, value in vars(self).items()])
        return f"ProductInfoClass(\n{formatted_string})"
    
    def setFavouritesInfo(self, attachement = '', user = -1):
        
        self.attachement = attachement
        self.user = user

    def setReleaseDate(self, releaseDate):
        self.releaseDate = releaseDate

    def setName(self, name):
        self.name = name

    def setSeller(self, seller):
        self.seller = seller

    def set_country(self, country:OrdersConsts.OrderTypes):
        self.country = country

    def copy(self):
        newCopy = ProductInfoClass(
            id=self.id,
            itemPrice=self.itemPrice,
            tax=self.tax,
            itemPriceWTax=self.itemPriceWTax,
            shipmentPrice=self.shipmentPrice,
            page=self.page,
            mainPhoto=self.mainPhoto,
            name=self.name,
            endTime=self.endTime,
            siteName=self.siteName,
            posredCommission=self.posredCommission,
            posredCommissionValue=self.posredCommissionValue,
            isMembershipNeeded=self.isMembershipNeeded,
            blitz = self.blitz,
            seller = self.seller,
            goodRate = self.goodRate,
            badRate = self.badRate,
            releaseDate = self.releaseDate,
            priceForFreeShipment = self.priceForFreeShipment,
        )

        newCopy.setFavouritesInfo(attachement = self.attachement, user = self.user)

        return newCopy
        