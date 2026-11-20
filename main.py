import os
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from loguru import logger
from tqdm import tqdm

from db.base import configure_database, session_scope
from db.exceptions import ApplicationException, BusinessException
from db.models import ExceptionType, ItemStatus, Run, now
from db.repository import (
    complete_run,
    create_run,
    get_work_items,
    record_attempt,
    register_input_file,
    run_output_file,
    start_run,
)
from IDXClient import IDXClient
from utils.logging import setup_logging, setup_screenshots
from workflow import process_invoice, reset

import argparse  
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:  
    parser = argparse.ArgumentParser(  
        prog="itemized-statements",  
        description="This process is a replacement for the Sutherland RPA bot that printed itemized statements from IDX.",  
    )  
    parser.add_argument(  
        "-d", "--file-date",  
        default=datetime.today().strftime("%Y%m%d"),  
        help="Input file date in YYYYMMDD format (default: today)",  
    )  
    parser.add_argument(  
        "--headless",  
        action="store_true",  
        help="Run the IDX client in headless mode",  
    )  
    parser.add_argument(  
        "-r", "--retry-failed-only",  
        action="store_true",  
        help="Only reprocess items that failed in a previous run",  
    )  
    parser.add_argument(  
        "--dry-run",  
        action="store_true",  
        help="Route DB writes to STAGING_DATABASE_URL and pass dry_run to the workflow",  
    )  
    return parser.parse_args(argv)

def main(file_date: str, 
         retry_failed_only: bool = False,
         headless: bool = True,
         dry_run: bool = False) -> None:
    default_database_url = os.getenv("DATABASE_URL", "sqlite:///itemized_statements.db")

    if dry_run:
        staging_database_url = os.getenv("STAGING_DATABASE_URL")
        if not staging_database_url:
            raise ValueError("dry_run=True requires STAGING_DATABASE_URL to be set")
        configure_database(staging_database_url)
        logger.info("dry_run=True: database routed to STAGING_DATABASE_URL")
    
    # check that file_date is in YYYYMMDD format
    if not file_date.isdigit() or len(file_date) != 8:
        raise ValueError("file_date must be in YYYYMMDD format")
    
    try:
        datetime.strptime(file_date, "%Y%m%d")
    except ValueError:
        raise ValueError("file_date must be in YYYYMMDD format")
    
    file_name = f'{file_date}_PAANS_BOT_v2.csv'
    file_path = '//NASDATA201/SHAREDATA/MV-RCR01/SHARED/RC Experience/DO NOT REMOVE - HCx Ontario Reports'
    csv_path = os.path.join(file_path, file_name)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input file not found: {csv_path}")

    # ── Transaction 1: create the run, load inputs ──────────────  
    with session_scope() as session:  
        run = create_run(session, file_name) # ! sets status = loaded  
        run_id = run.run_id  
        loaded = register_input_file(session, csv_path, run_id)  
        logger.info(f"Run {run_id} (#{run.run_id} on {file_name}), {loaded} new rows")

    # ── Transaction 2: flip to in_process, grab the work list ───  
    with session_scope() as session:  
        start_run(session, run_id) # ! sets status = in_process
        work = get_work_items(session, 
                              run_id, 
                              retry_failed_only=retry_failed_only)  
        if not work:
            raise BusinessException(f'No accounts to work for run {run_id}')
        
        run = session.get(Run, run_id)
        if not run:
            raise ApplicationException(f"Run {run_id} not found")
        run.total_records = len(work)

    # ── Transactions ──────────────────────  
    fatal = None  
    try:  
        
        idx_client = IDXClient(
            username = os.environ['IDX_USERNAME'],
            password = os.environ['IDX_PASSWORD'],
            headless=headless
        )
        
        idx_client.login_page.login()
        idx_client.settings_page.change_group(2)
        
        idx_client.vtb_page.select_vtb_option("Patient Services")
        
        for item in tqdm(work):  
            started = now() 
            
            try:  
                process_invoice(idx_client, 
                                item.invoice_number, 
                                item.group_number,
                                dry_run)
            
                end_time = now()
                status: ItemStatus = ItemStatus.SUCCESS
                exception_type: ExceptionType | None = None
                exception_reason: str | None = None
            except BusinessException as e:
                end_time = now()
                status = ItemStatus.FAILED
                exception_type = ExceptionType.BUSINESS
                exception_reason = str(e)[:4000]  
            except ApplicationException as e:  
                end_time = now()
                
                # take a screenshot if running headless
                if idx_client.headless:
                    idx_client.driver.save_screenshot(f"./logs/screenshots/{end_time.strftime('%Y%m%d')}/{end_time.strftime('%Y%m%d_%H%M%S')} - {item.invoice_number}.png")
                
                status = ItemStatus.FAILED
                exception_type = ExceptionType.APPLICATION
                exception_reason = f"{type(e).__name__}: {e}"[:4000]
                
                reset(idx_client=idx_client)
            except Exception as e:  # noqa: BLE001
                end_time = now()
                
                # take a screenshot if running headless
                if idx_client.headless:
                    idx_client.driver.save_screenshot(f"./logs/screenshots/{end_time.strftime('%Y%m%d')}/{end_time.strftime('%Y%m%d_%H%M%S')} - {item.invoice_number}.png")
                
                status = ItemStatus.FAILED
                exception_type = ExceptionType.PYTHON
                exception_reason = f"{type(e).__name__}: {e}"[:4000]
                
                reset(idx_client=idx_client)

            with session_scope() as session:  
                record_attempt(session, run_id=run_id,  
                               invoice_number=item.invoice_number,  
                               group_number=item.group_number,  
                               start_time=started,
                               end_time=end_time,
                               status=status,
                               exception_type=exception_type,
                               exception_reason=exception_reason)

    except Exception as e:  
        # error happens outside of individual invoice processing and is likely not linked to a specific invoice
        fatal = f"{type(e).__name__}: {e}"
        end_time = now()

        idx_client.driver.save_screenshot(f"./logs/screenshots/{end_time.strftime('%Y%m%d')}/{end_time.strftime('%Y%m%d_%H%M%S')} - fatal error.png")
        raise  
    finally:  
        # Close the run after processing all invoices
        with session_scope() as session:  
            complete_run(session, run_id, failure_reason=fatal) 
            df = run_output_file(session, file_name)

            outputs_dir = '//NT2KWB972SRV03/SHAREDATA/CPP-Data/CBO Westbury Managers/LEADERSHIP/Bot Folder/Part B/Itemized Statements'
            df.to_excel(f"{outputs_dir}/Transaction Report - {file_date}.xlsx", index=False)

        if dry_run:
            configure_database(default_database_url)
            logger.info("dry_run=True: database routing restored to DATABASE_URL")

def cli(argv: list[str] | None = None) -> None:  
    load_dotenv(find_dotenv(usecwd=True))  
    args = parse_args(argv)

    setup_logging("./logs")  
    setup_screenshots("./logs/screenshots")

    try:  
        main(  
            file_date=args.file_date,  
            retry_failed_only=args.retry_failed_only,  
            dry_run=args.dry_run,
            headless=args.headless 
        )  
    except BusinessException as e:  
        logger.warning(f"Business exception: {e}")  
        sys.exit(2)  
    except Exception:  
        logger.exception("Run failed")  
        sys.exit(1)
  
if __name__ == "__main__":
    load_dotenv()
    args = parse_args()
    
    setup_logging('./logs')
    setup_screenshots('./logs/screenshots')
    
    try:  
        main(  
            file_date=args.file_date,  
            retry_failed_only=args.retry_failed_only,  
            dry_run=args.dry_run,  
        )  
    except BusinessException as e:  
        logger.warning(f"Business exception: {e}")  
        sys.exit(2)  
    except Exception:  
        logger.exception("Run failed")  
        sys.exit(1)  