from confings.Consts import CURRENCY_API, CURRENT_POSRED
from APIs.utils import getHeader
import requests
import json


def getCurrentCurrencyRate():
    """Получить текущий курс рубля по отношению к йене

    Returns:
        float: курс рубля
    """
    headers = getHeader()
    page = requests.get(CURRENCY_API[CURRENT_POSRED], headers=headers)
    js = json.loads(page.text)


    for json_item in js:
        if json_item['codeTo'] == 'RUB':
            return float(json_item['rate'])