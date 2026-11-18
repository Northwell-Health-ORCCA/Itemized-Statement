from selenium import webdriver
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger
from dotenv import load_dotenv
import os
from pathlib import Path
import time

from pages.login import LoginPage
from pages.settings import SettingsPage
from pages.vtb import VTBPage
from pages.patient_services import PatientServices

class IDXClient:
    CHROME_SCALE_FACTOR = 0.75
    REMOTE_DEBUG_PORT = 9222
    BATCH_OPEN_RETRY_SLEEP = 2
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        
        self.driver = self._create_chrome_driver()
        self.login_page = LoginPage(self.driver)
        self.settings_page = SettingsPage(self.driver)
        self.vtb_page = VTBPage(self.driver)
        self.patient_services = PatientServices(self.driver)

        
    def _create_chrome_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome WebDriver based on environment settings.
        
        Returns:
            Configured Chrome WebDriver instance
        """
        options = webdriver.ChromeOptions()
        options.add_argument(f"--force-device-scale-factor={self.CHROME_SCALE_FACTOR}")
        options.add_argument("--start-maximized")
        
        if os.getenv("ENVIRONMENT", "").lower() == "production":
            # options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        else:
            # Add remote debugging for non-production
            options.add_argument(f"--remote-debugging-port={self.REMOTE_DEBUG_PORT}")
        
        return webdriver.Chrome(options=options)
    
    