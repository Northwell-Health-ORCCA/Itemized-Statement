# Imports and DotEnv
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
from pages.patient_services.demand_statement import DemandStatement
from pages.patient_services.invoice_list import InvoiceList
from pages.patient_services.select_invoices import SelectInvoices
from pages.patient_services.device_selection import DeviceSelection

load_dotenv()

# Constants
INPUT_FILE_PATH = '//NT2KWB972SRV03/SHAREDATA/CPP-Data/CBO Westbury Managers/LEADERSHIP/Bot Folder/ORCCA Rejection Scripting'
CHROME_SCALE_FACTOR = 0.75
REMOTE_DEBUG_PORT = 9222
BATCH_OPEN_RETRY_SLEEP = 2  # seconds
LOG_RETENTION_DAYS = 7  # Keep logs for 7 days
VTB_OPTION = 'Patient Services'
LOG_PATH = Path('C:\\PyProjects\\Itemized-Statement\\logs')
TEST_PT_INV = "P100755538"
TEST_PT_GRP = 3

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

#Login & change group 2, then open Patient Services in VTB
driver = create_chrome_driver()
login_page = LoginPage(driver)
try:
    if not login_page.login():
        raise ValueError("Login failed")
except Exception as e:
    logger.error(f"Login failed: {e}")
    raise ValueError("Login failed")

settings_page = SettingsPage(driver)
settings_page.change_group(2)

vtb_page = VTBPage(driver)
vtb_page.select_vtb_option("Patient Services")

#loop start here
# Search for Patient, Navigate to Patient Inquiry, Select Group
patient_services = PatientServices(driver)
patient_id = TEST_PT_INV
group_number = TEST_PT_GRP
patient_services.navigate_to_patient_inquiry(patient_id, group_number)

# Navigate to Demand Statement, Fill out form and navigate to Select invoices
invoice_list = InvoiceList(driver)
invoice_list.navigate_to_demand_statement()
demand_statement = DemandStatement(driver)
demand_statement.demand_statement(driver)

# Select invoice and confirm demand statement
select_invoices = SelectInvoices(driver)
invoice = TEST_PT_INV
if 'P' in invoice:
    inv_num = str(invoice[1:])
else:
    inv_num = str(invoice)
logger.debug(f"Searching for invoice: {inv_num}")
select_invoices.search_for_invoice(inv_num)
demand_statement._click_ok()

# select device and save output if printed to new screen
device_selection = DeviceSelection(driver, device_name=None)
device_selection.select_device()
vtb_page = VTBPage(driver)
vtb_page.select_vtb_option("Patient Services")
