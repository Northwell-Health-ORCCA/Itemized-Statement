import time

from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from db.exceptions import ApplicationException
from pages.base import BasePage
from pages.pt_services.demand_statement import DemandStatement
from pages.pt_services.device_selection import DeviceSelection
from pages.pt_services.invoice_list import InvoiceList
from pages.pt_services.select_invoices import SelectInvoices


class PatientServices(BasePage):
    PATIENT_PROMPT = (By.ID, "PatientPrompt")
    PATIENT_INQUIRY_HYPER = (By.ID, "lnkPatientInquiry")
    PATIENT_INQUIRY_HEADER = (
        By.CLASS_NAME, 
        "fe_c_heading.fe_c_heading--section.fe_c_accordion-item__heading-text"
        )
    INVOICE_LIST_KEY = (By.ID, "selectorActionCodeI")
    
    def __init__(self, driver):
        self.driver = driver
        
        self.demand_statement = DemandStatement(self.driver)
        self.device_selection = DeviceSelection(self.driver)
        self.invoice_list = InvoiceList(self.driver)        
        self.select_invoices = SelectInvoices(self.driver)
        

    def _click_magnifier(self):
        magnifier = WebDriverWait(self.driver, 1).until(
            EC.presence_of_element_located((By.ID, "cmdNavPtLkp"))
        )
        magnifier.click()

    def _confirm_new_patient_selected(self, patient_id, element):
        patient_prompt = element
        patient_name = patient_prompt.get_attribute('value')
        return patient_name == patient_id

    def _enter_patient_prompt(self, patient_id: str):
        try:
            patient_prompt = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.PATIENT_PROMPT)
            )
            patient_prompt.click()
            time.sleep(.5)
            patient_prompt.send_keys(Keys.CONTROL, "a")
            time.sleep(.5)

            patient_prompt.send_keys(f'-{patient_id}')
            patient_prompt.send_keys(Keys.TAB)

            # if not self._confirm_new_patient_selected(patient_id, patient_prompt):
            #     logger.warning(f"Patient ID {patient_id} not selected correctly")
            #     raise ApplicationException(f"Patient ID {patient_id} not selected correctly")
            return
        except TimeoutException:
            logger.error(f"Timeout while trying to select Patient ID {patient_id}")
            raise ApplicationException(f"Timeout while trying to select Patient ID {patient_id}")
        
    def _select_patient_inquiry(self):
        try:
            patient_inquiry = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.PATIENT_INQUIRY_HYPER)
            )
            time.sleep(.5)
            patient_inquiry.click()
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.PATIENT_INQUIRY_HEADER)
            )
            
            logger.debug("Patient Inquiry selected")
            return 
        except TimeoutException:
            logger.error("Timeout while trying to select Patient Inquiry")
            return 
        
    def _select_invoice_list(self, group_number: str = "3"):
        try:
            invoices = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.INVOICE_LIST_KEY)
            )
            invoices.click()
            group_num_prompt = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".fe_is-required"))
                )
            group_num_prompt.click()
            time.sleep(.5)
            group_num_prompt.send_keys(group_number)
            time.sleep(.5)
            ok_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, 'OK'))
            )
            ActionChains(self.driver).click(ok_button).perform()

        except TimeoutException:
            logger.error("Timeout while trying to select Invoice List")

    def navigate_to_patient_inquiry(self, patient_id: str, group_number: str = "3"):
        self._enter_patient_prompt(patient_id)
        self._select_patient_inquiry()
        self._select_invoice_list(group_number)

