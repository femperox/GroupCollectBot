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
            driver.execute_script("document.activeElement.click();")
            time.sleep(10)
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
        
        item = {}
        
        driver = WebUtils.getSelenium(wire = False)
        try:
            driver.get(url)
            AmazonApi.changeZipCode(driver = driver)
            #WebUtils.wait_for_page_update(driver = driver)
            
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
            driver.quit()
            return item

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
            '''
        except Exception as e:
            pprint(e)
        finally:
            return item

