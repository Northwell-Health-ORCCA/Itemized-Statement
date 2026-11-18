from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common import keys
import time
from loguru import logger
import helper_methods


class DemandStatement:
    STMT_FORMAT_ELEMENT = (By.ID, 'sAf12')
    STMT_VALUE = 109
    SELECT_INVOICES = (By.CSS_SELECTOR, '#sAf7r1 > div.css-b62m3t-container > div > div.rcm-select__indicators.css-1wy0on6')
    SELECT_INVOICES_VALUE = "Y"
    LISTBOX = (By.CSS_SELECTOR, '#sAf7r1 > div.css-b62m3t-container > div > div.rcm-select__indicators.css-1wy0on6')
    LISTBOX_OPTIONS_ELEMENT = (By.CSS_SELECTOR, '#sAf7r1')


    def __init__(self, driver):
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
    
    def _send_value_to_field(self, field_element, value):
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

    def _select_invoices(self):
            helper_methods.change_option_in_listbox(
                self.driver,
                target_name="Y",
                listbox_open=self.SELECT_INVOICES,
                listbox_element=self.LISTBOX,
                current_selection_element=self.LISTBOX,
                listbox_options_element=self.LISTBOX_OPTIONS_ELEMENT
            )

    def demand_statement(
            self, 
            stmt_element: tuple = STMT_FORMAT_ELEMENT, 
            stmt_value: int = STMT_VALUE,
            ):
        try:
            if self._confirm_demand_statement():
                self._send_value_to_field(stmt_element, stmt_value)
                self._select_invoices()

        except Exception as e:
            logger.error(f"Error while processing demand statement: {e}")
