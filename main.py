# Imports and DotEnv
from dotenv import load_dotenv
from loguru import logger
from selenium import webdriver
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
import os
import shutil
import time
from typing import List
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
from pathlib import Path
import time

from pages.login_page import LoginPage

from utils.chrome_driver import ChromeDriverFactory

load_dotenv()


# Constants

# INPUT_FILE_PATH = '' # need to make input a file path that can be user specified
CHROME_SCALE_FACTOR = 0.75
REMOTE_DEBUG_PORT = 9222
BATCH_OPEN_RETRY_SLEEP = 2  # seconds
LOG_RETENTION_DAYS = 7  # Keep logs for 7 days
VTB_OPTION = 'Patient Services'
LOG_PATH = Path('C:\\PyProjects\\Itemized-Statement\\logs')

#Setup Logging
def setup_logging(log_folder_path: Path) -> None:
    """Configure loguru logger with file outputs for debug and info levels.
    
    Args:
        log_folder_path: Directory where log files will be saved
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H %M")
    debug_path = log_folder_path / f"debug_{timestamp}.log"
    info_path = log_folder_path / f"info_{timestamp}.log"
    
    logger.remove()
    logger.add(
        debug_path,
        rotation="5 MB",
        level="DEBUG",
        backtrace=True,
        diagnose=True,
        retention="3 days",
        compression="zip"
    )
    logger.add(
        info_path,
        rotation="5 MB",
        level="INFO",
        retention="3 days",
        compression="zip"
    )

#Setup Chrome Driver
def create_chrome_driver() -> webdriver.Chrome:
    """Create and configure Chrome WebDriver based on environment settings.
    
    Returns:
        Configured Chrome WebDriver instance
    """
    options = webdriver.ChromeOptions()
    options.add_argument(f"--force-device-scale-factor={CHROME_SCALE_FACTOR}")
    options.add_argument("--start-maximized")
    
    if os.getenv("ENVIRONMENT", "").lower() == "production":
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
    else:
        # Add remote debugging for non-production
        options.add_argument(f"--remote-debugging-port={REMOTE_DEBUG_PORT}")
    
    return webdriver.Chrome(options=options)

def login_to_idx() -> None:
    driver = create_chrome_driver()
    login_page = LoginPage(driver)
    # login_page.navigate_to_login()
    # user = os.environ['IDX_USERNAME']
    # password = os.environ['IDX_PASSWORD']
    try:
        if not login_page.login(): 
            raise ValueError("Login failed")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise ValueError("Login failed")

def clear_and_send_keys(element, text):
    element.clear()
    element.send_keys(text)
    
def main():
    print("Hello from itemized-statement!")


if __name__ == "__main__":
    main()
