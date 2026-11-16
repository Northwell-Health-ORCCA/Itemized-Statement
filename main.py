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


# Constants
INPUT_FILE_PATH = '//NT2KWB972SRV03/SHAREDATA/CPP-Data/CBO Westbury Managers/LEADERSHIP/Bot Folder/ORCCA Rejection Scripting'
CHROME_SCALE_FACTOR = 0.75
REMOTE_DEBUG_PORT = 9222
BATCH_OPEN_RETRY_SLEEP = 2  # seconds
LOG_RETENTION_DAYS = 7  # Keep logs for 7 days
VTB_OPTION = 'Patient Services'
LOG_PATH = Path('C:\\PyProjects\\Itemized-Statement\\logs')

def clear_and_send_keys(element, text):
    element.clear()
    element.send_keys(text)
    
def main():
    print("Hello from itemized-statement!")


if __name__ == "__main__":
    main()
