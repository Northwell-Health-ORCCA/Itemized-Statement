from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger
from dotenv import load_dotenv
from traitlets import Bool
from typing import Optional
load_dotenv()
import os

from helper_methods import clear_and_send_keys

class LoginPage:
    
    # 1. Locators
    USERNAME_INPUT = (By.ID, 'username')
    PASSWORD_INPUT = (By.ID, 'password')
    LOGIN_BUTTON = (By.ID, 'pfh-login-module-button-login')
    

    def __init__(self, driver):
        self.driver = driver
        self.URL = os.environ['IDX_URL']
        self.USER = os.environ['IDX_USERNAME']
        self.PASSWORD = os.environ['IDX_PASSWORD']
        self.navigate_to_login()

    def navigate_to_login(self) -> None:
        self.driver.get(self.URL)
    
    def _attempt_login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        if username is None:
            username = self.USER
        if password is None:
            password = self.PASSWORD
        if username is None and password is None:
            logger.error("IDX_USERNAME and IDX_PASSWORD must be provided")
            raise ValueError("IDX_USERNAME and IDX_PASSWORD must be provided")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(self.USERNAME_INPUT))
        username_input = self.driver.find_element(*self.USERNAME_INPUT)
        clear_and_send_keys(username_input, username)

        password_input = self.driver.find_element(*self.PASSWORD_INPUT)
        clear_and_send_keys(password_input, password)

        login_button = self.driver.find_element(*self.LOGIN_BUTTON)

        login_button.click()

        try:
            error = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"p.alert-block.error"))
            )
            error_text = error.text
            logger.error(f"Login error message: {error_text}")
            raise Exception("Login failed - invalid credentials")
        except TimeoutException:
            logger.info("No login error message displayed.")
            return True


    def _confirm_login(self) -> bool:
        try:
            WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.ID, "vtbToggleButton"))
            )
            logger.success("Login confirmed.")
            return True
        except TimeoutException:
            logger.error("Login confirmation failed.")
            return False

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Attempt to log in with the provided username and password.

        Args:
            username: Optional username to use for login. Defaults to environment variable.
            password: Optional password to use for login. Defaults to environment variable.

        Returns:
            True if login is successful, False otherwise.
        """
        if not self._attempt_login(username, password):
            return False
        return self._confirm_login()