from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from loguru import logger

from pages.base import BasePage
    
class VTBPage(BasePage):
    VTB_BUTTON = (By.ID, "vtbToggleButton")
    VTB_CONTAINER = (By.CSS_SELECTOR, "div.vtb-container open")
    
    HEADER_DICT = {
        'Patient Services': ((By.ID, "lblLabel62"), "Patient Services")}
    
    def __init__(self, driver):
        super().__init__(driver)

    def _get_vtb_options(self) -> dict:
        options = {}
        options_obj = self.driver.find_element(By.CLASS_NAME, "vtb-items")
        buttons = options_obj.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            options[button.text] = (By.ID, button.get_attribute('id'))
        return options

    def _is_vtb_open(self):
        try:  
            button = self.driver.find_element(*self.VTB_BUTTON)  
            return button.get_attribute('title') == 'Close Menu'  
        except:  
            return False  

    def _toggle_vtb(self) -> None:
        self.driver.find_element(*self.VTB_BUTTON).click()

    def _confirm_navigation(self, option_text, h_text) -> None: 
        try:
            wait = WebDriverWait(self.driver, 10)
            locator = self.HEADER_DICT[option_text][0]  
            wait.until(  
                EC.text_to_be_present_in_element(locator, h_text)  
            )  
            logger.success(f"Navigation to '{option_text}' confirmed with header text '{h_text}'.")
        except:
            logger.error(f"Failed to confirm navigation to '{option_text}' with header text '{h_text}'.")
            raise Exception("Navigation to the selected VTB option failed.")
    
    def select_vtb_option(self, option_text) -> None:
        """
        Select a VTB option by its visible text.

        Args:
            option_text: The visible text of the VTB option to select.

        Raises:
            ValueError: If the specified option is not found in the VTB options.
        """
        if not self._is_vtb_open():
            self._toggle_vtb()

        self.VTB_OPTIONS = self._get_vtb_options()
        
        if option_text in self.VTB_OPTIONS:
            option_locator = self.VTB_OPTIONS[option_text]
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(option_locator)
            ).click()
        else:
            raise ValueError(f"Option '{option_text}' not found in VTB options.")

        self.modal.close_modal()
        h_text = self.HEADER_DICT[option_text][1]
        self._confirm_navigation(option_text, h_text)
        time.sleep(1)
        
        if self._is_vtb_open():
            logger.debug("VTB is still open, closing it now.")
            self._toggle_vtb()