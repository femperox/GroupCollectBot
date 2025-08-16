class NewsInfoClass:

    def __init__(self, id, news_url, images_list = [], origin = None, price = None, title = '',
                 release_date = None, additional_dates_list = [], additional_urls_list = [], 
                 prices_list = [], **kwargs):
        
        self.id = id
        self.title = title
        self.news_url = news_url
        self.images_list = images_list
        self.origin = origin
        self.price = price
        self.prices_list = prices_list
        self.release_date = release_date
        self.additional_dates_list = additional_dates_list
        self.additional_urls_list = additional_urls_list

    def __bool__(self):
        return bool(self.id) and bool(self.origin)

    def __repr__(self):
        formatted_string = "\n".join([f"'{attr}': {value}," for attr, value in vars(self).items()])
        return f"ProductInfoClass(\n{formatted_string})"