

from selenium import webdriver
from loguru import logger
import time
from main import BATCH_OPEN_RETRY_SLEEP, VTB_OPTION

from pages.vtb import VTBPage
from pages.login import LoginPage
from pages.settings import SettingsPage

def recover_from_fatal_error(
    driver: webdriver.Chrome,
    settings_page: SettingsPage,
    vtb: VTBPage,
    login_page: LoginPage,
    group: int,
    username: str,
    password: str
) -> bool:
    """Attempt to recover from fatal error by logging out and back in.
    
    Args:
        driver: Selenium WebDriver instance
        settings_page: Settings page object
        vtb: VTB page object
        pp_batch: Payment posting batch page object
        login_page: Login page object
        group: Group number to restore
        username: IDX username
        password: IDX password
        
    Returns:
        True if recovery succeeded, False otherwise
    """
    try:
        logger.warning("Attempting recovery: logging out and back in...")
        
        # Try to logout
        try:
            settings_page.logout()
            time.sleep(2)
        except Exception as logout_error:
            logger.warning(f"Logout failed during recovery: {logout_error}")
        
        # Re-login
        login_page.navigate_to_login()
        time.sleep(2)
        
        if not login_page.login(username, password):
            logger.error("Login failed during recovery")
            return False
        
        logger.info("Successfully logged back in")
        
        # Restore group and VTB selection
        settings_page.change_group(group)
        time.sleep(1)
        
        if not vtb.validate_current_selection(VTB_OPTION):
            vtb.select_vtb_option(VTB_OPTION)
        
        logger.success("Recovery successful - ready to continue processing")
        return True
        
    except Exception as e:
        logger.error(f"Recovery failed: {e}")
        return False