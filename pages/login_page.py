from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger
from dotenv import load_dotenv
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

    def navigate_to_login(self) -> None:
        self.driver.get(self.URL)

    def login(self, username: str, password: str) -> None:
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(self.USERNAME_INPUT))
        username_input = self.driver.find_element(*self.USERNAME_INPUT)
        clear_and_send_keys(username_input, username)

        password_input = self.driver.find_element(*self.PASSWORD_INPUT)
        clear_and_send_keys(password_input, password)

        login_button = self.driver.find_element(*self.LOGIN_BUTTON)

        login_button.click()

        try:
            error = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"p.alert-block.error"))
            )
            error_text = error.text
            logger.error(f"Login error message: {error_text}")
            raise Exception("Login failed - invalid credentials")
        except TimeoutException:
            logger.info("No login error message displayed.")
            return 