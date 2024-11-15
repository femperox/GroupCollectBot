import re
from confings.Consts import RegexType

class StoreSelectorParent:

    url = ''

    def getStoreName(self):
        '''
        Возвращает название сайта (его домен)

        :param url: ссылка на товар
        :return:
        '''
        name = re.findall(RegexType.regex_store_url, self.url)[0][2:-1]
        name = name.replace('jp','').replace('com','').replace('www', '').replace('co', '').replace('order.', '').replace('.','')
        return name
    
    
    def getItemID(self):
        """Получить id товара в магазине

        Returns:
            string: id товара
        """

        id = self.url.split('/')[-1]
        id= id.split('?_')[0].split('?pr_prod_strat')[0]
        id = id.replace('?source_location=share', '').replace('&utm_source=web&utm_medium=share', '').replace('detail.php?product_id=', '')
        id = id.replace('?scode=', '').replace('?gcode=', '').replace('item?itemCode=', '').replace('detail', '')
        return id

