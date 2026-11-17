from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
from loguru import logger


class SettingsPage:

    MENU_BUTTON = (By.ID, "user_menu_btn-button")
    HOG_SCREEN_LINK = (By.ID, "tools_HOG_1")
    GROUP_SELECTOR = (By.ID, "cboGroup")
    CURRENT_SELECTION = (By.CSS_SELECTOR, "[class^='rcm-select__single-value']")
    OK_BTN = (By.ID, "cmdOK")
    CANCEL_BTN = (By.ID, "cmdCancel")
    LOGOUT_BTN = (By.ID, "user_logout")
    VIEW_SELECTOR = (By.ID, "cboView")
    VIEW_LISTBOX = (By.CSS_SELECTOR, "[class^='rcm-select__menu']")

    def __init__(self, driver):
        self.driver = driver

    def _open_listbox_menu (self):
        if not self._is_view_listbox_present():
            view_selector = self.driver.find_element(*self.VIEW_SELECTOR)
            view_selector.click()
            time.sleep(0.5)
            logger.debug('View options menu opened.')
    
    def _is_view_listbox_present(self):
        try:
            self.driver.find_element(*self.VIEW_LISTBOX)
            logger.debug('View listbox is present.')
            return True
        except:
            logger.debug('View listbox is not present.')
            return False

    def _get_listbox_options(self):
        if not self._is_view_listbox_present():
            self._open_listbox_menu()
            
        listbox = self.driver.find_element(*self.VIEW_LISTBOX)
        divs = listbox.find_elements(By.TAG_NAME, "div")
        
        self.CURRENT_SELECTION = divs[0].text if divs else None
        self.VIEW_OPTIONS = divs
        
        logger.debug(f'View options retrieved: {[option.text for option in self.VIEW_OPTIONS]}')
        logger.debug(f'Current selection: {self.CURRENT_SELECTION}')

    def change_option_in_listbox(self, target_view_name: str):
        self._get_listbox_options()
        
        selected_view = self.CURRENT_SELECTION
        # get the index of the currently selected view
        selected_index = None
        for i, option in enumerate(self.VIEW_OPTIONS):
            if selected_view in option.text:
                selected_index = i
                break
        
        # find the item in the list that contains the target view name
        target_index = None
        for i, option in enumerate(self.VIEW_OPTIONS):
            if target_view_name in option.text:
                target_index = i
                break
        
        if target_index is None or selected_index is None:
            logger.error(f"Target view '{target_view_name}' not found in view options.")
            raise ValueError(f"Target view '{target_view_name}' not found in view options.")
        
        actions = ActionChains(self.driver)
        difference = target_index - selected_index
        presses = abs(difference)
        
        if difference > 0:
            actions.send_keys(Keys.ARROW_DOWN * presses)
        elif difference < 0:
            actions.send_keys(Keys.ARROW_UP * presses)
        
        actions.send_keys(Keys.ENTER)
        actions.perform()
        logger.success(f"View changed to '{target_view_name}'.")

    def logout(self):
        # check if any modal is open
        MODAL_OK = (By.ID, "modalButtonOk")
        try:
            self.driver.find_element(*MODAL_OK).click()
        except NoSuchElementException:
            pass
        self._open_listbox_menu()
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located(self.LOGOUT_BTN)
        ).click()

    def change_group(self, group: int) -> None:
        # Implement logic to change the group
        pass