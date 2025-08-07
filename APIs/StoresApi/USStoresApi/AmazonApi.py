from APIs.webUtils import WebUtils 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from APIs.posredApi import PosredApi
from datetime import datetime
from dateutil.relativedelta import relativedelta
from confings.Consts import PosrednikConsts, OrdersConsts
from pprint import pprint
import time

class AmazonApi:

    freeDeliveryPrice = 35

    currentDeliveryIndex = PosrednikConsts.USA_DELIVERY_INDEX

    def changeZipCode(driver):
        driver.save_screenshot("1screenshotamz.png")
        try:
            zip_code_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "glow-ingress-line2"))
            )
            zip_code_button.click()

            zip_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "GLUXZipUpdateInput"))
            )
            zip_input.clear()
            zip_input.send_keys(AmazonApi.currentDeliveryIndex)

            apply_button = driver.find_element(By.ID, "GLUXZipUpdate")
            apply_button.click()
            
            time.sleep(5)
            driver.execute_script("document.activeElement.click();")
            time.sleep(5)

        except Exception as e:
            print(f"Ошибка: {e}")

    def parseAmazonItem(url, item_id):
        
        driver = WebUtils.getSelenium(wire = False)
        driver.get(url)
        AmazonApi.changeZipCode(driver = driver)

        item = {}

        try:
            item['itemPrice'] = float(driver.find_element(By.CSS_SELECTOR, "span.a-offscreen").get_attribute("textContent").replace('$', ''))
        except:
            item['itemPrice'] = float(driver.find_element(By.CSS_SELECTOR, "span.a-price.aok-align-center").get_attribute("textContent").replace('$', ''))
        item['id'] = item_id

        item['tax'] = 0
        item['itemPriceWTax'] = 0
        item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.free if item['itemPrice'] >= AmazonApi.freeDeliveryPrice else OrdersConsts.ShipmentPriceType.undefined
        item['page'] = WebUtils.cleanUrl(url)
        item['mainPhoto'] = driver.find_element(By.ID, "landingImage").get_attribute("src")
        item['name'] = driver.find_element(By.ID, "productTitle").text
        item['endTime'] = datetime.now() + relativedelta(years=3)
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
        return item

