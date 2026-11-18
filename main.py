from pathlib import Path
from glob import glob
from tqdm import tqdm
from datetime import datetime
import os

from db.base import session_scope  
from db.models import ExceptionType, ItemStatus, Run, RunStatus, now  
from db.repository import (  
    complete_run, create_run, get_work_items, record_attempt, register_input_file, reconcile, run_summary, start_run  
)

from db.exceptions import BusinessException, ApplicationException
from workflow import process_invoice


def main(file_date: str, retry_failed_only: bool = False) -> None:  
    # check that file_date is in YYYYMMDD format
    if not file_date.isdigit() or len(file_date) != 8:
        raise ValueError("file_date must be in YYYYMMDD format")
    
    try:
        datetime.strptime(file_date, "%Y%m%d")
    except ValueError:
        raise ValueError("file_date must be in YYYYMMDD format")
    
    file_name = f'{file_date}_PAANS_BOT_v2.csv'
    file_path = f'//NASDATA201/SHAREDATA/MV-RCR01/SHARED/RC Experience/DO NOT REMOVE - HCx Ontario Reports'
    csv_path = os.path.join(file_path, file_name)

    # ── Transaction 1: create the run, load inputs ──────────────  
    with session_scope() as session:  
        run = create_run(session, file_name) #! sets status = loaded  
        run_id = run.run_id  
        loaded = register_input_file(session, csv_path, run_id)  
        print(f"Run {run_id} (#{run.run_id} on {file_name}), {loaded} new rows")

    # ── Transaction 2: flip to in_process, grab the work list ───  
    with session_scope() as session:  
        start_run(session, run_id) #! sets status = in_process
        work = get_work_items(session, run_id, retry_failed_only=retry_failed_only)  
        if not work:
            raise BusinessException(f'No accounts to work for run {run_id}')
        
        run = session.get(Run, run_id)
        if not run:
            raise ApplicationException(f"Run {run_id} not found")
        run.total_records = len(work)

    # ── Transactions ──────────────────────  
    fatal = None  
    try:  
        for item in work:  
            started = now() 
            
            try:  
                process_invoice(item.invoice_number, item.group_number)
            
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
                status = ItemStatus.FAILED
                exception_type = ExceptionType.APPLICATION
                exception_reason = f"{type(e).__name__}: {e}"[:4000]
            except Exception as e:
                end_time = now()
                status = ItemStatus.FAILED
                exception_type = ExceptionType.PYTHON
                exception_reason = f"{type(e).__name__}: {e}"[:4000]

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
        raise  
    finally:  
        # Close the run after processing all invoices
        with session_scope() as session:  
            complete_run(session, run_id, failure_reason=fatal) 
            print(run_summary(session, run_id))  
            
if __name__ == "__main__":
    today = datetime.today().strftime('%Y%m%d')
    main(today)