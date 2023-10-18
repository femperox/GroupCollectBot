def parsePayPay(url):

    curl = f'https://paypayfleamarket.yahoo.co.jp/api/item/v2/items/{getItemID(url)}'

    headers = getHeader()
    page = requests.get(curl, headers=headers)
    js = page.json()

    item = {}
    item['priceYen'] = js['price']
    item['percentTax'] = 0
    item['priceShipmt'] = 0
    item['page'] = url
    item['mainPhoto'] = js['images'][0]['url']
    item['siteName'] = 'payPayFleamarket'

    return item