from selenium import webdriver
from loguru import logger

from utils.config import *

from pages.login import LoginPage
from pages.settings import SettingsPage
from pages.vtb import VTBPage
from pages.patient_services import PatientServices

class IDXClient:
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        
        self.driver = self._create_chrome_driver()
        self.login_page = LoginPage(self.driver, self.username, self.password)
        self.settings_page = SettingsPage(self.driver)
        self.vtb_page = VTBPage(self.driver)
        self.patient_services = PatientServices(self.driver)

        
    def _create_chrome_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome WebDriver based on environment settings.
        
        Returns:
            Configured Chrome WebDriver instance
        """
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless=new')
        # options.add_argument('--no-sandbox')
        options.add_argument(f"--force-device-scale-factor={CHROME_SCALE_FACTOR}")
        options.add_argument("--start-maximized")
        # options.add_argument(f"--remote-debugging-port={REMOTE_DEBUG_PORT}")
        
        return webdriver.Chrome(options=options)
    
    