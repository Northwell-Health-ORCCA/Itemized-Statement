import os
from selenium import webdriver

from main import CHROME_SCALE_FACTOR, REMOTE_DEBUG_PORT


class ChromeDriverFactory:

    def __init__(self):
        self.chrome_scale_factor = CHROME_SCALE_FACTOR
        self.remote_debug_port = REMOTE_DEBUG_PORT
        self.create_chrome_driver()

    def create_chrome_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome WebDriver based on environment settings.
        
        Returns:
            Configured Chrome WebDriver instance
        """
        options = webdriver.ChromeOptions()
        options.add_argument(f"--force-device-scale-factor={self.chrome_scale_factor}")
        options.add_argument("--start-maximized")
        
        if os.getenv("ENVIRONMENT", "").lower() == "production":
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        else:
            # Add remote debugging for non-production
            options.add_argument(f"--remote-debugging-port={self.remote_debug_port}")
        
        return webdriver.Chrome(options=options)