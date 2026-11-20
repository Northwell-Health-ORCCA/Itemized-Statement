from pathlib import Path
from loguru import logger
from datetime import datetime

def setup_screenshots(screenshots_folder_path: Path | str) -> None:
    """Create a directory for storing screenshots."""
    date = datetime.now().strftime("%Y-%m-%d")
    
    if isinstance(screenshots_folder_path, str):
        screenshots_folder_path = Path(screenshots_folder_path)
    screenshots_folder_path = screenshots_folder_path / date
    screenshots_folder_path.mkdir(parents=True, exist_ok=True)

def setup_logging(log_folder_path: Path | str) -> None:
    """Configure loguru logger with file outputs for debug and info levels.
    
    Args:
        log_folder_path: Directory where log files will be saved
    """
    if isinstance(log_folder_path, str):
        log_folder_path = Path(log_folder_path)
    log_folder_path.mkdir(parents=True, exist_ok=True)
    debug_path = log_folder_path / "debug_{time:YYYYMMDD}.log"
    info_path = log_folder_path / "info_{time:YYYYMMDD}.log"
    
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