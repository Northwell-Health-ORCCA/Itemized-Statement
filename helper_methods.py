from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time


from loguru import logger

def clear_and_send_keys(element, text):
    element.clear()
    element.send_keys(text)

def _open_listbox_menu (driver, listbox_open):
    try:
        wait = WebDriverWait(driver, 1)
        wait.until(EC.element_to_be_clickable(listbox_open)).click()
        logger.debug('Listbox menu opened.')
    except:
        logger.error('Failed to open listbox menu.')

def _is_view_listbox_present(driver, listbox_element):
    try:
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located(listbox_element))
        logger.debug('Listbox is present.')
        return True
    except:
        logger.debug('Listbox is not present.')
        return False

def _get_listbox_options(
        driver, 
        listbox_open, #element to open the listbox
        listbox_element, #base element for detection
        current_selection_element, #element showing the current selection
        listbox_options_element #parent element containing the listbox options
        ):
    if not _is_view_listbox_present(driver, listbox_element):
        _open_listbox_menu(driver, listbox_open)

    parent_div = driver.find_element(*listbox_options_element)
    hidden_div = parent_div.find_elements(By.CLASS_NAME, "rcm-select-hidden-div")
    child_divs = hidden_div[0].find_elements(By.TAG_NAME, "div") if hidden_div else []
    listbox_options = [child.get_attribute('textContent') for child in child_divs] 
    logger.debug(f'View options retrieved: {listbox_options}')
  

    current_selection = driver.find_element(*current_selection_element).get_attribute("textContent")
    
    logger.debug(f'Current selection: {current_selection}')

    return current_selection, listbox_options

def change_option_in_listbox(
        driver, 
        target_name: str, 
        listbox_open, #element to open the listbox
        listbox_element, #base element for detection
        current_selection_element, #element showing the current selection
        listbox_options_element #parent element containing the listbox options
        ):
    current_selection, listbox_options = _get_listbox_options(
        driver, listbox_open, 
        listbox_element, 
        current_selection_element, 
        listbox_options_element
        )

    selected_view = current_selection
    # get the index of the currently selected view
    selected_index = None
    for i, option in enumerate(listbox_options):
        if selected_view in option:
            selected_index = i
            # logger.debug(f'Selected index found: {selected_index}')
            break
    
    # find the item in the list that contains the target view name
    target_index = None
    for i, option in enumerate(listbox_options):
        if target_name in option:
            target_index = i
            # logger.debug(f'Target index found: {target_index}')
            break
    
    if target_index is None or selected_index is None:
        logger.error(f"Target option '{target_name}' not found in list of options.")
        raise ValueError(f"Target option '{target_name}' not found in list of options.")
    
    actions = ActionChains(driver)
    difference = target_index - selected_index
    # logger.debug(f'Difference between target and selected index: {difference}')
    presses = abs(difference)
    # logger.debug(f'Number of key presses required: {presses}')
    _open_listbox_menu(driver, listbox_open)
    listbox_element_obj = driver.find_element(*listbox_open)

    key_to_send = "\ue015" if difference > 0 else "\ue013"  
    direction = "DOWN" if difference > 0 else "UP"  
    logger.debug(f'Sending ARROW_{direction} key {presses} times.')

    for _ in range(presses):  
        logger.debug(f'Sending ARROW_{direction} key.')
        listbox_element_obj.send_keys(key_to_send)  
        logger.debug(f'Sent ARROW_{direction} key.')
        time.sleep(0.35)  # give the UI time to register/update each press
    
    logger.debug(f'Sending ENTER key to select the option.')
    listbox_element_obj.send_keys(Keys.ENTER)

    logger.debug(f'Sending ENTER key through ActionChains.')
    actions.send_keys(Keys.ENTER)
    actions.perform()
    logger.success(f"Option changed to '{target_name}'.")