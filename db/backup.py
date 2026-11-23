import os  
import shutil  
import sqlite3  
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configuration
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///itemized_statements.db") 
DB_NAME = DB_PATH.split("///")[-1] 
BACKUP_DIR = os.getcwd() + "/backups"  
RETENTION_DAYS = 7


def run_backup():  
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # 1. Create the backup file with a timestamp  
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  
    backup_filepath = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")

    # Simple file copy (safe because RPA is idle)  
    shutil.copy2(DB_NAME, backup_filepath)  
    print(f"Backup created: {backup_filepath}")

    # 2. Delete backups older than 7 days  
    now = datetime.now()  
    for filename in os.listdir(BACKUP_DIR):  
        if filename.startswith("backup_") and filename.endswith(".db"):  
            file_path = os.path.join(BACKUP_DIR, filename)  
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))  
            if now - file_mtime > timedelta(days=RETENTION_DAYS):  
                os.remove(file_path)  
                print(f"Deleted old backup: {filename}")


if __name__ == "__main__":  
    run_backup()