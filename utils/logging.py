from pathlib import Path
from loguru import logger
from datetime import datetime

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