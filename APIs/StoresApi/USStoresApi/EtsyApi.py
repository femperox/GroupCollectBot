from APIs.webUtils import WebUtils 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from confings.Consts import PosrednikConsts, OrdersConsts
from selenium.common.exceptions import TimeoutException
from APIs.PosredApi.posredApi import PosredApi
import time 
import json

class EtsyApi:

    currentDeliveryIndex = PosrednikConsts.USA_DELIVERY_INDEX

    def changeZipCode(driver):
        """TODO: Вылетает капча, подумать как переделать. Не критичино
        Изменить индекс на адрес склада

        Args:
            driver (seleniumwire.webdriver.Chrome): драйвер

        Returns:
            bool: результат смены индекса
        """

        try:

            element = driver.find_element(By.ID, "shipping_and_returns")
            driver.execute_script("arguments[0].scrollIntoView();", element)
            time.sleep(1)
            shipping_details_button_selector = "button[data-content-toggle-uid='data-estimated-shipping-form-fields']"
            time.sleep(1)
            shipping_details_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, shipping_details_button_selector))
            )
            shipping_details_button.click()
            time.sleep(1)

            zip_input = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "estimated-shipping-zip-code"))
            )
            zip_input.clear()
            zip_input.send_keys(PosrednikConsts.USA_DELIVERY_INDEX)

            update_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='estimated-shipping-submit-button'][type='submit']"))
                    )
            update_button.click()
            time.sleep(3)
            time.sleep(3)
            driver.save_screenshot('off.png')
            return True
            
        except TimeoutException:
            print("Не удалось изменить почтовый индекс")
            return False
        except Exception as e:
            print(f"Ошибка при смене индекса: {e}")
            return False
        

    def getItemInfo(rawText):
        """Получить список <script type='application/ld+json'>

        Args:
            rawText (string): html-текст страницы

        Returns:
            bs4.element.ResultSet: список <script type='application/ld+json'>
        """
        
        soup = WebUtils.getSoup(rawText = rawText)
        return soup.findAll('script', type='application/ld+json')
        
    def parseEtsy(url):
        """Получение базовой информации о товаре с etsy

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """
        item = {}
        curl = WebUtils.cleanUrl(url=url)
        try:
            display = WebUtils.getDisplay()
            display.start()
            proxy = WebUtils.getRandomPrivateProxy()
            driver = WebUtils.getSelenium(isUC=True, proxy = proxy.selenium)
            driver.uc_open_with_reconnect(curl, reconnect_time=10)
            js = EtsyApi.getItemInfo(rawText = driver.page_source)
            display.stop()
            driver.quit() 

            if js:
                js = json.loads(js[0].text) 
                item['status'] = OrdersConsts.StoreStatus.in_stock if 'InStock' in js['offers']['availability'] else OrdersConsts.StoreStatus.sold
                '''TODO: После фикса капчи на доставке
                if item['status'] in [OrdersConsts.StoreStatus.in_stock]:
                        
                        js = EtsyApi.getItemInfo(rawText = driver.page_source)
                        if js:
                            js = json.loads(js[1].text) 
                        else:
                            driver.quit()  
                            return item 
     
                    else:
                        driver.quit()  
                        return item 
                '''
        
                item['itemPrice'] = float(js['offers']['price']) if 'price' in js['offers'] else float(js['offers']['lowPrice'])
                item['page'] = curl
                item['mainPhoto'] = js['image'][0]['contentURL']
                item['name'] = js['name']
                item['siteName'] = OrdersConsts.Stores.etsy
                item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
                item['id'] = js['sku']

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
            print(e)
        finally:
            driver.quit() 
            return item