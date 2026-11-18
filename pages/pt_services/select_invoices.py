import time

from loguru import logger
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SelectInvoices:
    def __init__(self, driver):
        self.driver = driver
        self.BASE_ACTION_CODES = {
            "F": (By.ID, "selectorActionCodeF"),
            "R": (By.ID, "selectorActionCodeR"),
        }

    # confirm on select invoices
    def _confirm_on_select_invoices(self):
        locator_tuple = (
            By.CSS_SELECTOR,
            "#selector-collapsible-form > ul > li > div.fe_c_accordion-item__header.fe_is-expanded > h3"
        )
        WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(locator_tuple))
        
        if self.driver.find_element(*locator_tuple):
            logger.debug("Select invoices section is present.")
            return True
        logger.debug("Select invoices section is not present.")
        return False

    #filter invoices

    def _select_action_code(self, action_code: str):
        if action_code in self.BASE_ACTION_CODES:
            try:
                action_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable(self.BASE_ACTION_CODES[action_code])
                )
                ActionChains(self.driver).click(action_button).perform()
                logger.debug(f"Clicked action code '{action_code}' button.")
            except TimeoutException:
                logger.error(f"Timeout while trying to click action code '{action_code}' button.")
        else:
            logger.error(f"Action code '{action_code}' not found in base action codes.")
            raise ValueError(f"Action code '{action_code}' not found in base action codes.")

    def _confirm_invoice_filtered(self, invoice_number=None):
        locator_tuple = (
            By.CSS_SELECTOR,
            "#rcm-dbms-selector > div > div > div.ag-root-wrapper.ag-ltr.ag-layout-normal > div.ag-root-wrapper-body.ag-focus-managed.ag-layout-normal > div.ag-root.ag-unselectable.ag-layout-normal.ag-body-horizontal-content-no-gap > div.ag-body.ag-layout-normal > div.ag-body-viewport.ag-row-animation.ag-layout-normal > div.ag-pinned-left-cols-container > div.ag-row-odd.ag-row.ag-row-level-0.ag-row-position-absolute.ag-row-last.ag-row-not-inline-editing.ag-row-focus"
        )
        inv_row_element = WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located(locator_tuple)
        )
        logger.debug("Parent div for invoice filtering located.")
        if invoice_number:
            try:
                inv_num_element = inv_row_element.find_element(  
                    By.CSS_SELECTOR,  
                    "#rcm-dbms-selector > div > div > div.ag-root-wrapper.ag-ltr.ag-layout-normal > div.ag-root-wrapper-body.ag-focus-managed.ag-layout-normal > div.ag-root.ag-unselectable.ag-layout-normal.ag-body-horizontal-content-no-gap > div.ag-body.ag-layout-normal > div.ag-body-viewport.ag-row-animation.ag-layout-normal > div.ag-pinned-left-cols-container > div.ag-row-odd.ag-row.ag-row-level-0.ag-row-position-absolute.ag-row-last.ag-row-not-inline-editing.ag-row-focus > div.ag-cell.ag-cell-not-inline-editing.ag-cell-normal-height.ag-cell-last-left-pinned.ag-cell-value"  
                )
                if inv_num_element and inv_num_element.text.__contains__(invoice_number):
                    logger.debug(f"Invoice row for '{invoice_number}' found.")
                    return inv_row_element
            except NoSuchElementException:
                logger.debug(f"Invoice row for '{invoice_number}' not found.")
                return False
        logger.debug("No invoice number provided for filtering.")
        return False

    def _select_check_box(self, element: WebElement):
        if element:
            element.find_element(
                By.CSS_SELECTOR, 
                "input.fe_c_checkbox__input"
                ).send_keys(Keys.SPACE)
            logger.debug("Checkbox selected.")

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


    def search_for_invoice(self, invoice_number=None):
        if self._confirm_on_select_invoices():
            self._select_action_code("F")

        parent_div = WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located((By.ID, "rcm-dbms-bottom-form-canvas"))
        )
        invoice_element = WebDriverWait(parent_div, 3).until(
            EC.presence_of_element_located((By.ID, "sAf1"))
        )

        if invoice_number:
            invoice_element.send_keys(invoice_number)
            invoice_element.send_keys(Keys.RETURN)

        time.sleep(0.5)
        invoice_filtered = self._confirm_invoice_filtered(invoice_number)
        time.sleep(0.5)
        if invoice_filtered:
            checkbox = invoice_filtered.find_element(By.CSS_SELECTOR, "input.fe_c_checkbox__input")
            self._select_check_box(invoice_filtered)
            logger.debug("Checkbox selection attempted.")
            is_checked = checkbox.get_attribute("aria-checked") == "true"  
            logger.debug(f"Checkbox is_checked status: {is_checked}")
            if is_checked:
                self._click_ok()
                time.sleep(0.5)
                self._click_ok()
                return True
            return False
        return False
