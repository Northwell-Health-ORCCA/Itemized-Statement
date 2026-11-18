from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common import keys
import time
from loguru import logger

class InvoiceList:
    
    FILTER_FIELDS = {
        1: 'sAf1r1',
        2: 'sAf1r2'
    }
    OPERATOR_FIELDS = {
        1: 'sAf2r1',
        2: 'sAf2r2'
    }
    VALUE_FIELDS = {
        1: 'sAf3r1',
        2: 'sAf3r2'
    }

    BASE_ACTION_CODES = {
        "1": (By.ID, "selectorActionCode1"), #multigroup view
        "B": (By.ID, "selectorActionCodeB"), #all/bal/cred bal
        "D": (By.ID, "selectorActionCodeD"), #view detail
        "E": (By.ID, "selectorActionCodeE"), #expand/contract
        "F": (By.ID, "selectorActionCodeF"), #filter
        "G": (By.ID, "selectorActionCodeG"), #reversal invoices
        "H": (By.ID, "selectorActionCodeH"), #chg crts/splits
        "I": (By.ID, "selectorActionCodeI"), #more inquiries
        "O": (By.ID, "selectorActionCodeO"), #oldest/newest
        "Q": (By.ID, "selectorActionCodeQ"), #q filter
        "T": (By.ID, "selectorActionCodeT"), #more actions
        "W": (By.ID, "selectorActionCodeW"), #edi
        "Z": (By.ID, "selectorActionCodeZ") #multi inv detail
    }
    MORE_INQ_ACTION_CODES = {
        "BACK": (By.ID, "backButton"), #back button
        "3": (By.ID, "selectorActionCode3"), #category info
        "4": (By.ID, "selectorActionCode4"), #outsource info
        "5": (By.ID, "selectorActionCode5"), #experian info
        "6": (By.ID, "selectorActionCode6"), #spv prov audit trail
        "7": (By.ID, "selectorActionCode7"), #ref prov audit trail
        "8": (By.ID, "selectorActionCode8"), #manage wcnf charges
        "A": (By.ID, "selectorActionCodeA"), #pmt auth inq
        "D": (By.ID, "selectorActionCodeD"), #dictionary inq
        "F": (By.ID, "selectorActionCodeF"), #financial inq
        "M": (By.ID, "selectorActionCodeM"), #comments
        "N": (By.ID, "selectorActionCodeN"), #abn requests
        "P": (By.ID, "selectorActionCodeP"), #patient inq
        "R": (By.ID, "selectorActionCodeR"), #pricing module
        "T": (By.ID, "selectorActionCodeT"), #tasks
        "Y": (By.ID, "selectorActionCodeY"), #tes inq
        "Z": (By.ID, "selectorActionCodeZ") #archive task note
    }
    MORE_ACTIONS_ACTION_CODES = {
        "BACK": (By.ID, "backButton"), #back button
        "1": (By.ID, "selectorActionCode1"), #print ledgers etm
        "B": (By.ID, "selectorActionCodeB"), #acct bal by fsc
        "D": (By.ID, "selectorActionCodeD"), #demand statement
        "G": (By.ID, "selectorActionCodeG"), #demand claim
        "H": (By.ID, "selectorActionCodeH"), #statement history
        "I": (By.ID, "selectorActionCodeI"), #ins clm rqst
        "L": (By.ID, "selectorActionCodeL"), #print ledgers
        "N": (By.ID, "selectorActionCodeN"), #abn requests
        "Y": (By.ID, "selectorActionCodeY"), #last pt pymts
    }

    def __init__(self, driver):
        self.driver = driver

    def _access_find_function(self):
        try:
            side_button = WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ag-side-button-button"))
            )
            side_button.click()
            time.sleep(.5)
            find = WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located((By.ID, "~F"))
            )
            find.click()
            time.sleep(.5)
        except TimeoutException:
            logger.error("Timeout while trying to find Invoice Number")

    def _filter_by_selector(
            self, operator: str='=', 
            selector: str='Invoice', 
            value: str='', 
            field_num: int=1
            ):
        try:
            self._set_selector(field_num=field_num, selector=selector)
            self._set_operator(field_num=field_num, operator=operator)
            self._set_value(field_num=field_num, value=value)
        except TimeoutException:
            logger.error(f"Timeout while trying to filter by {selector}")

    def _set_selector(self, field_num: int, selector: str='Invoice'):
        selector_find = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, self.FILTER_FIELDS[field_num]))
            )
        selector_find.click()
        selector_find.clear()
        selector_find.send_keys(selector)
        time.sleep(0.5)

    def _set_operator(self, field_num: int, operator: str='='):
        operator_find = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, self.OPERATOR_FIELDS[field_num]))
            )
        operator_find.click()
        operator_find.clear()
        operator_find.send_keys(operator)
        time.sleep(.5)
        TAB = '\ue004'
        operator_find.send_keys(TAB)

    def _set_value(self, field_num: int, value: str=''):
        value_find = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, self.VALUE_FIELDS[field_num]))
            )
        value_find.click()
        value_find.clear()
        value_find.send_keys(value)
        time.sleep(0.5)

    def _click_ok(self):
        ok_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, 'OK'))
            )
        ActionChains(self.driver).click(ok_button).perform()

    def _confirm_invoice_filtered(self, invoice_number: str):
        
        try:
            focused_row = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ag-row-focus'))
            )
            cells = focused_row.find_elements(By.CSS_SELECTOR, 'div.ag-cell-value')
            if cells:
                last_cell = cells[-1]
                if last_cell.get_attribute('title') == invoice_number:
                    logger.debug(f"Successfully found invoice {invoice_number} in the list.")
                else:
                    logger.error(f"Invoice {invoice_number} not found in the focused row.")
                    return False
                first_cell = cells[0]
                if first_cell.get_attribute('title') != invoice_number:
                    # find the class 'fe_c_checkbox__input'
                    checkbox = first_cell.find_element(By.CSS_SELECTOR, 'input.fe_c_checkbox__input')
                    # if aria_checked value of checkbox is false, send the space key to check it
                    if checkbox.get_attribute('aria-checked') == 'false':
                        checkbox.send_keys(keys.Keys.SPACE)
                        logger.debug(f"Checkbox for invoice {invoice_number} was not selected. Sent SPACE key to select it.")
                    else:
                        logger.debug(f"Checkbox for invoice {invoice_number} is already selected.")
                    return True
        except TimeoutException:
            logger.error("Timeout while trying to confirm filtered invoice.")
            return False
        
    def _select_action_code(self, action_code: str):
        if action_code in self.BASE_ACTION_CODES:
            try:
                action_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(self.BASE_ACTION_CODES[action_code])
                )
                ActionChains(self.driver).click(action_button).perform()
                logger.debug(f"Clicked action code '{action_code}' button.")
            except TimeoutException:
                logger.error(f"Timeout while trying to click action code '{action_code}' button.")
        else:
            logger.error(f"Action code '{action_code}' not found in base action codes.")

    def navigate_to_demand_statement(self):
        self._select_action_code("T")
        time.sleep(.15)
        self._select_action_code("D")