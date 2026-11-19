import csv
import os
import time

from dotenv import load_dotenv
from loguru import logger
from selenium.common import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from db.exceptions import ApplicationException


class DeviceSelection:

    def __init__(self, driver):  
        load_dotenv()  
        device_name = os.getenv('PRINTER_NAME', "")
        self.driver = driver  
        self.device_name = '' if not device_name else device_name

    def _insert_device_name(self, device_name) -> None:  
        locator_tuple = (By.ID, "sAf1")  
        device_input_field = WebDriverWait(self.driver, 3).until(  
            EC.presence_of_element_located(locator_tuple)  
        )  
        logger.debug(f"Device name input located for '{device_name}'.")
        # get current value of field
        current_value = device_input_field.get_attribute('value')
        logger.debug(f"Current device name in input field: '{current_value}'")
        if current_value == device_name:
            logger.debug("Device name is already set correctly.")
            return
        # TODO: clear() method not working, change to ctrl + a
        device_input_field.clear()  
        device_input_field.send_keys(device_name)
        device_input_field.send_keys(Keys.TAB)  
        logger.debug(f"Device name '{device_name}' entered.")

    def _switch_window(self, expected_url, timeout=5):  
        def _window_with_url(driver):  
            for handle in driver.window_handles:  
                driver.switch_to.window(handle)  
                if expected_url in driver.current_url:  
                    return handle  
            return False

        handle = WebDriverWait(self.driver, timeout).until(_window_with_url)  
        logger.debug(f"Switched to window with URL containing '{expected_url}'.")  
        return handle  

    def _click_ok(self):
        time.sleep(0.15)
        try:
            ok_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, 'OK'))
            )
            ok_button.click()
            logger.debug("Clicked OK button to show invoice queued.")
        except TimeoutException:
            logger.error("Timeout while trying to click OK button.")

    def _close_new_window(self) -> None:  
        orig_window = self.driver.current_window_handle
        try:
            self._switch_window(
                expected_url="https://nsli-prod.rcm.athenahealth.com/rcm/window.html",
                timeout=5
            )
        except TimeoutException:
            logger.warning("Timeout while trying to switch to new window.")
            raise ApplicationException("Failed to switch to new window.")

        locator_tuple = (By.CSS_SELECTOR, "body > div.popup-window-content > div > div")  
        element = WebDriverWait(self.driver, 3).until(  
            EC.presence_of_element_located(locator_tuple)  
        )  
        logger.debug("Copying text from modal.")  
        body_text = element.text  
        # logger.debug(f"Copied text: {body_text}")

        logger.debug("Saving copied text to CSV in logs folder.")  
        os.makedirs('logs', exist_ok=True)  
        with open('logs/print_confirmation_log.csv', 'a', newline='') as csvfile:  
            writer = csv.writer(csvfile)  
            writer.writerow([body_text])

        self.driver.switch_to.window(orig_window)

    def _confirm_on_inv_list(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "selectorHeader"))
            )
            logger.debug("Confirmed we are back on the invoice list screen.")
        except TimeoutException:
            logger.error("Failed to confirm invoice list screen.")

    def select_device(self) -> None:  
        self._insert_device_name(self.device_name)
        self._click_ok()
        if self.device_name in (None, ''):
            self._close_new_window()
        self._confirm_on_inv_list()
        
