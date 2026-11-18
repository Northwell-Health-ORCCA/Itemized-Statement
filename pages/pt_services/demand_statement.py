import time

from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common import keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class DemandStatement:
    STMT_FORMAT_ELEMENT = (By.ID, 'sAf12')
    STMT_VALUE = "109"
    SELECT_INVOICES = (By.CSS_SELECTOR, '#sAf7r1 > div.css-b62m3t-container > div > div.rcm-select__indicators.css-1wy0on6')
    SELECT_INVOICES_VALUE = "Y"
    LISTBOX = (By.CSS_SELECTOR, '#sAf7r1 > div.css-b62m3t-container > div > div.rcm-select__indicators.css-1wy0on6')
    LISTBOX_OPTIONS_ELEMENT = (By.CSS_SELECTOR, '#sAf7r1')


    def __init__(self, driver: WebDriver):
        self.driver = driver

    def _confirm_demand_statement(self) -> bool:
        try:
            demand_claim_header = WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located((By.ID, 'formHeader'))
            )
            demand_claim_header_text = demand_claim_header.text
            if "Demand/Reprint Patient Statement" in demand_claim_header_text:
                logger.debug("Successfully navigated to Demand Claim page.")
                return True
            else:
                logger.error("Demand Claim header is not displayed. Display Text: " + demand_claim_header_text)
                return False
        except TimeoutException:
            logger.error("Timeout while trying to confirm navigation to Demand Claim page.")
            return False
    
    def _send_value_to_field(self, field_element: tuple, value: str):
        try:
            field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(field_element)
            )
            if field:
                field.send_keys(keys.Keys.CONTROL, "a")
                time.sleep(.15)
                field.send_keys(str(value))
                time.sleep(0.15)
                TAB = '\ue004'
                field.send_keys(TAB)
                logger.debug(f"Successfully sent value {value} to field.")
            else:
                logger.error("Field element not found.")
        except TimeoutException:
            logger.error("Timeout while trying to send value to field.")
            return False
        return True
    
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
        
    def _click_cancel(self):
        time.sleep(0.15)
        try:
            close_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, 'rcmLookupBoxButtonClose'))
            )
            close_button.click()
            logger.debug("Clicked CLOSE button to continue to printer selection.")
        except TimeoutException:
            logger.error("Timeout while trying to click CLOSE button.")


    def demand_statement(self):
        try:
            if self._confirm_demand_statement():
                self._send_value_to_field(self.STMT_FORMAT_ELEMENT, self.STMT_VALUE)
                parent_div = self.driver.find_element(By.ID, 'sAf7r1')
                clickable_element = parent_div.find_element(
                    By.CSS_SELECTOR, 
                    '#sAf7r1 > div.css-b62m3t-container'
                    )
                #click and send "Y" to the element using action chain
                action = ActionChains(self.driver)
                TAB = '\ue004'
                action.move_to_element(clickable_element
                                       ).click().send_keys("Y").send_keys(TAB).perform()
                logger.debug("Clicked on the clickable element within the parent div.")
                logger.debug("Sent 'Y' to the clickable element.")

                    
                time.sleep(0.35)

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error while processing demand statement: {e}")
