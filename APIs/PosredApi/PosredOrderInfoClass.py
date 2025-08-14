from confings.Consts import OrdersConsts

class PosredOrderInfoClass:

    def __init__(self, product_id = '', posred_id = '', title = '', tracking_id = '',
                 parcel_id = '', status = '', posred_url = '', **kwargs):
        
        self.product_id = product_id
        self.tracking_id = tracking_id
        self.parcel_id = parcel_id
        self.posred_id = posred_id
        self.title = title
        self.status = status
        self.posred_url = posred_url

    def __bool__(self):
        return bool(self.product_id) and bool(self.posred_id)
    
    def __repr__(self):
        formatted_string = "\n".join([f"'{attr}': {value}," for attr, value in vars(self).items()])
        return f"PosredOrderInfoClass(\n{formatted_string})"

    def set_posred_url(self, url):

        self.posred_url = url