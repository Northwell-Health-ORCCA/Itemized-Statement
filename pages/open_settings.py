from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from loguru import logger

from pages.base import BasePage


class SettingsPage(BasePage):

    MENU_BUTTON = (By.ID, "user_menu_btn-button")
    HOG_SCREEN_LINK = (By.ID, "tools_HOG_1")
    GROUP_SELECTOR = (By.ID, "cboGroup")
    OK_BTN = (By.ID, "cmdOK")
    CANCEL_BTN = (By.ID, "cmdCancel")
    LOGOUT_BTN = (By.ID, "user_logout")
    LISTBOX = (By.XPATH, "//*[@id='cboGroup']/div[1]/div/div[1]")
    LISTBOX_OPTIONS = (By.XPATH, '//*[@id="cboGroup"]/div[1]/div/div[1]/div')

    def __init__(self, driver):
        self.driver = driver

    def _open_settings(self):
        wait = WebDriverWait(self.driver, 2)
        wait.until(
            EC.presence_of_element_located(self.MENU_BUTTON)
        ).click()

    def _open_hog_screen(self):
        wait = WebDriverWait(self.driver, 2)
        wait.until(
            EC.presence_of_element_located(self.HOG_SCREEN_LINK)
        ).click()

    def logout(self):
        # check if any modal is open
        MODAL_OK = (By.ID, "modalButtonOk")
        try:
            self.driver.find_element(*MODAL_OK).click()
        except NoSuchElementException:
            pass
        self._open_settings()
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located(self.LOGOUT_BTN)
        ).click()

    def change_group(self, group: int) -> None:
        self._open_settings()
        self._open_hog_screen()
        self.change_option_in_listbox(
            target_name=str(group),
            listbox_open=self.GROUP_SELECTOR,
            listbox_element=self.LISTBOX,
            current_selection_element=self.LISTBOX,
            listbox_options_element=self.GROUP_SELECTOR
        )