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

class EbayApi:

    currentDeliveryIndex = PosrednikConsts.USA_DELIVERY_INDEX

    def changeZipCode(driver):
        """Изменить индекс на адрес склада

        Args:
            driver (seleniumwire.webdriver.Chrome): драйвер

        Returns:
            bool: результат смены индекса
        """

        try:
            shipping_details_button_selector = "button[data-testid='ux-action'][data-clientpresentationmetadata*='SHIPPING_RETURNS_PAYMENTS_TAB_MODULE']"

            shipping_details_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, shipping_details_button_selector))
            )
            shipping_details_button.click()
            time.sleep(1)

            country_select_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "shCountry"))
            )
            country_select = Select(country_select_element)
            country_select.select_by_visible_text("United States")

            zip_input = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "shZipCode"))
            )
            zip_input.clear()
            zip_input.send_keys(PosrednikConsts.USA_DELIVERY_INDEX)

            update_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn--primary[data-ebayui][type='submit']"))
                    )
            update_button.click()
            time.sleep(3)
            driver.refresh()
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
        
    def parseEbayItem(url):
        """Получение базовой информации о товаре с ebay

        Args:
            url (string): ссылка на товар

        Returns:
            dict: словарь с информацией о товаре
        """

        item = {}
        try:
            driver = WebUtils.getSelenium(isUC = True, block_img = True)
            driver.get(url)
            js = EbayApi.getItemInfo(rawText = driver.page_source)
            if js:
                js = json.loads(js[1].text) 
                item['status'] = OrdersConsts.StoreStatus.in_stock if 'InStock' in js['offers']['availability'] else OrdersConsts.StoreStatus.sold
                
                if item['status'] in [OrdersConsts.StoreStatus.in_stock]:
                    if EbayApi.changeZipCode(driver = driver):
                        js = EbayApi.getItemInfo(rawText = driver.page_source)
                        if js:
                            js = json.loads(js[1].text) 
                        else:
                            driver.quit()  
                            return item 
                    else:
                        driver.quit()  
                        return item 
                item['itemPrice'] = float(js['offers']['price'])
                item['page'] = WebUtils.cleanUrl(js['offers']['url'])
                item['mainPhoto'] = js['image'][0]
                item['name'] = js['name']
                item['status'] = OrdersConsts.StoreStatus.in_stock if 'InStock' in js['offers']['availability'] else OrdersConsts.StoreStatus.sold
                item['siteName'] = OrdersConsts.Stores.ebay

                if 'shippingDetails' in js['offers'] and js['offers']['shippingDetails']:
                    item['shipmentPrice'] = float(js['offers']['shippingDetails'][0]['shippingRate']['value'])
                else:
                    item['shipmentPrice'] = OrdersConsts.ShipmentPriceType.undefined
                item['id'] = item['page'].split('/')[-1]

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