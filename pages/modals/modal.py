import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from loguru import logger

class Modal():    
    def __init__(self, driver):
        self.driver = driver
        
        self.modal_window = (By.CLASS_NAME, 'fe_c_overlay__dialog.fe_c_modal__dialog.fe_c_modal__dialog--large.fe_c_modal__dialog--padded.fe_is-info')
        self.ok_btn = (By.ID, 'modalButtonOk')
        
    def _detect_window(self):
        try:
            self.driver.find_element(*self.modal_window)
        except NoSuchElementException:
            return False
        return True
    
    def _extract_modal_text(self):
        return self.driver.find_element(*self.modal_window).text
    
    def close_modal(self):
        time.sleep(0.5)
        if self._detect_window():
            modal_text = self._extract_modal_text()
            logger.debug(f'Closing modal with text: {modal_text}')
            self.driver.find_element(*self.ok_btn).click()