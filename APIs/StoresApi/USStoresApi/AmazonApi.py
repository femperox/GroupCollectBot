from APIs.webUtils import WebUtils 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from APIs.PosredApi.posredApi import PosredApi
from datetime import datetime
from dateutil.relativedelta import relativedelta
from confings.Consts import PosrednikConsts, OrdersConsts
from pprint import pprint
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class AmazonApi:

    freeDeliveryPrice = 35

    currentDeliveryIndex = PosrednikConsts.USA_DELIVERY_INDEX

    def changeZipCode(driver, timeout=5):
        """DEPRECATED

        Args:
            driver (_type_): _description_
            timeout (int, optional): _description_. Defaults to 5.

        Returns:
            _type_: _description_
        """

        try:
            # Используем более быстрые селекторы
            zip_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.ID, "glow-ingress-line2"))
            )
            zip_button.click()

            zip_input = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "GLUXZipUpdateInput"))
            )
            zip_input.clear()
            zip_input.send_keys(AmazonApi.currentDeliveryIndex)

            # Найти кнопку по тексту или ID
            apply_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.ID, "GLUXZipUpdate"))
            )
            apply_button.click()
            
            # Ждем немного и кликаем вне формы
            #driver.execute_script("document.activeElement.click();")
            driver.refresh()
            return True
            
        except TimeoutException:
            print("Не удалось изменить почтовый индекс")
            return False
        except Exception as e:
            print(f"Ошибка при смене индекса: {e}")
            return False
        
    def parseBuyingOptions(driver):

        see_all_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'See All Buying Options')]"))
        )
        if not see_all_button:
            return -1
        see_all_button.click()
        WebUtils.wait_for_page_update(driver)

        # Ждём загрузки цен
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.a-offscreen"))
        )

        # Ищем все цены
        prices = driver.find_elements(By.CSS_SELECTOR, "span.a-offscreen")
        price_values = []

        for price in prices:
            try:
                price_text = price.text.strip().replace('$', '').replace(',', '')
                if price_text and price_text.replace('.', '', 1).isdigit():
                    price_values.append(float(price_text))
            except:
                continue

        # Находим минимальную цену
        if price_values:
            return min(price_values)
        else:
            return None
                
    def parseAmazonItem(url, item_id):
        """DEPRECATED

        Args:
            url (_type_): _description_
            item_id (_type_): _description_

        Returns:
            _type_: _description_
        """
        
        item = {}
        
        driver = WebUtils.getSelenium(wire = False, block_img = True)
        try:
            driver.get(url)
            AmazonApi.changeZipCode(driver = driver)

            #WebUtils.wait_for_page_update(driver = driver)
            #driver.save_screenshot("screenshot2.png")
            '''
            html_content = driver.page_source
            driver.quit()
            soup = WebUtils.getSoup(rawText=html_content)
            price_elements = ['a-offscreen', 'a-price aok-align-center', 'aok-offscreen', 'priceValue']
            
            item['itemPrice'] = None
            for element in price_elements:
                if element == 'priceValue':
                    soup_elem = soup.find('input', id=element)
                else:
                    soup_elem = soup.find('span', class_=element)
                if soup_elem:
                    if element == 'priceValue':
                        item['itemPrice'] = float(soup_elem.get_attribute('value').replace('$', ''))
                    else:
                        item['itemPrice'] = float(soup_elem.text.replace('$', ''))
                    break
            if not item['itemPrice'] and soup.find('a', string = 'See All Buying Options'):
                item['itemPrice'] = 111111
            else:
                item['itemPrice'] = -12

            item['id'] = item_id
            item['mainPhoto'] = soup.find('img', id = 'landingImage')['src']
            item['name'] = soup.find('span', id =  "productTitle").text.strip()
            item['siteName'] = OrdersConsts.Stores.amazon
            item['priceForFreeShipment'] = AmazonApi.freeDeliveryPrice
            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if item['itemPrice'] >= AmazonApi.freeDeliveryPrice else OrdersConsts.ShipmentPriceType.undefined
            item['page'] = WebUtils.cleanUrl(url)

            commission = PosredApi.getСommissionForItemUSD()
            if item['shipmentPrice'] in [OrdersConsts.ShipmentPriceType.free, OrdersConsts.ShipmentPriceType.undefined]:
                format_string = item['itemPrice']
                format_number = item['itemPrice']
            else:
                format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
                format_number = item['itemPrice'] + item['shipmentPrice']
            item['posredCommission'] = commission['posredCommission'].format(format_string)
            item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)
            

            return item
            '''
            try:
                item['itemPrice'] = float(driver.find_element(By.CSS_SELECTOR, "span.a-offscreen").get_attribute("textContent").replace('$', ''))
            except:
                item['itemPrice'] = float(driver.find_element(By.CSS_SELECTOR, "span.a-price.aok-align-center").get_attribute("textContent").replace('$', ''))
            item['id'] = item_id

            item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if item['itemPrice'] >= AmazonApi.freeDeliveryPrice else OrdersConsts.ShipmentPriceType.undefined
            item['page'] = WebUtils.cleanUrl(url)
            item['mainPhoto'] = driver.find_element(By.ID, "landingImage").get_attribute("src")
            item['name'] = driver.find_element(By.ID, "productTitle").text
            item['siteName'] = OrdersConsts.Stores.amazon
            item['priceForFreeShipment'] = AmazonApi.freeDeliveryPrice

            commission = PosredApi.getСommissionForItemUSD()
            if item['shipmentPrice'] in [OrdersConsts.ShipmentPriceType.free, OrdersConsts.ShipmentPriceType.undefined]:
                format_string = item['itemPrice']
                format_number = item['itemPrice']
            else:
                format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
                format_number = item['itemPrice'] + item['shipmentPrice']
            item['posredCommission'] = commission['posredCommission'].format(format_string)
            item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)
            driver.quit()
        except Exception as e:
            pprint(e)
        finally:
            return item
        
    def cleanPrice(price_string) -> float:
        """Конвертировать строку с ценой в число

        Args:
            price_string (string): строка с ценой

        Returns:
            float: цена-число
        """
        return float(price_string.replace('$', '').replace(',', '').strip())

    def loadDynamicList(url):
        """Прогрузить динамический список доступных айтемов

        Args:
            url (string): часть ссылки открывающей список

        Returns:
            BeautifulSoup: bs4 страница
        """

        proxy = WebUtils.getRandomPrivateProxy()
        display = WebUtils.getDisplay()
        display.start()
        driver = WebUtils.getSelenium(isUC=True, proxy = proxy.selenium)
        curl = 'https://www.amazon.com' + url
        
        driver.uc_open_with_reconnect(curl, reconnect_time=10)
        soup = WebUtils.getSoup(rawText = driver.page_source)
        
        driver.quit()
        display.stop()

        return soup

    def parseDynamicList(url):
        """Отпарсить динамический список товаров на стоимость товара и цену доставки

        Args:
            url (string): часть ссылки открывающей список

        Returns:
            List[float, float/ShipmentPriceType]: список: цена и доставка
        """
        
        soup = AmazonApi.loadDynamicList(url = url)
        offers = soup.find('div', id = 'aod-offer-list')
        itemPrice = None
        shipmentPrice = None
        if offers:
            offer_min = offers.find('div', id = 'aod-offer')
            if offer_min:
                itemPrice = AmazonApi.cleanPrice(offer_min.find('span', class_ = 'aok-offscreen').text)
                shipment_price = offer_min.find('span', {'data-csa-c-mir-type': 'DELIVERY'})
                shipmentPrice = OrdersConsts.ShipmentPriceType.free if shipment_price.get('data-csa-c-delivery-price') == 'FREE' else AmazonApi.cleanPrice(shipment_price.get('data-csa-c-delivery-price'))              
        return [itemPrice, shipmentPrice]
    
    def parseAmazonItemWProxy(url, item_id):
        """Получение базовой информации о товаре с Амазон

        Args:
            url (string): ссылка на товар
            item_id (string): id товара

        Returns:
            dict: словарь с информацией о товаре
        """

        httpx_client = WebUtils.getHttpxClient(isPrivateProxy = True, isExtendedHeader = True)
        response = httpx_client.get(url = url)
        if 'a.co' in url:
            time.sleep(2)
            httpx_client.get(url = WebUtils.cleanUrl(url = str(response.url)))
        httpx_client.close()

        item = {}

        try:
            soup = WebUtils.getSoup(rawText = response.text)
            price = soup.find('span', class_=lambda x: x and 'a-price' in x and 'aok-align-center' in x)
            item['itemPrice'] = None
            if price:
                try:
                    item['itemPrice'] = AmazonApi.cleanPrice(price.text)
                except:
                    price = soup.find('span', class_ = 'a-offscreen')
                    item['itemPrice'] = AmazonApi.cleanPrice(price.text)
                suposedShipment = soup.find('span', {'data-csa-c-delivery-benefit-program-id': 'paid_shipping'})
                if suposedShipment:
                    price = suposedShipment.get('data-csa-c-delivery-price') 
                    item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if price == 'FREE' else AmazonApi.cleanPrice(suposedShipment.get('data-csa-c-delivery-price'))
                else:
                    item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if item['itemPrice'] >= AmazonApi.freeDeliveryPrice else OrdersConsts.ShipmentPriceType.undefined
            else:
                other_options = soup.find('a', title ='See All Buying Options')
                if other_options:
                    # другие опции для покупки
                    item['itemPrice'], item['shipmentPrice']  = AmazonApi.parseDynamicList(url = other_options['href'])
                else:
                    other_options = soup.find('a', id ='aod-ingress-link')
                    if other_options:
                        item['itemPrice'], item['shipmentPrice']  = AmazonApi.parseDynamicList(url = other_options['href'])
                    else:
                        item['status'] = OrdersConsts.StoreStatus.sold

            if item['itemPrice']:
                item['status'] = OrdersConsts.StoreStatus.in_stock
                item['page'] = WebUtils.cleanUrl(url)
                item['mainPhoto'] = soup.find('img', id = "landingImage").get("src")
                item['name'] = soup.find('span', id = "productTitle").text.strip()
                item['siteName'] = OrdersConsts.Stores.amazon
                item['priceForFreeShipment'] = AmazonApi.freeDeliveryPrice
                item['id'] = item_id
                
                commission = PosredApi.getСommissionForItemUSD()
                if item['shipmentPrice'] in [OrdersConsts.ShipmentPriceType.free, OrdersConsts.ShipmentPriceType.undefined]:
                    format_string = item['itemPrice']
                    format_number = item['itemPrice']
                else:
                    format_string = f"( {item['itemPrice']} + {item['shipmentPrice']} )"
                    format_number = item['itemPrice'] + item['shipmentPrice']
                item['posredCommission'] = commission['posredCommission'].format(format_string)
                item['posredCommissionValue'] = commission['posredCommissionValue'](format_number)
        except Exception as e:
            pprint(e)
        finally:
            return item

