from pathlib import Path
from glob import glob
from tqdm import tqdm
from datetime import datetime

from db.base import session_scope  
from db.models import ExceptionType, ItemStatus, Run, RunStatus, now  
from db.repository import (  
    complete_run, create_run, get_work_items, record_attempt, register_input_file, reconcile, run_summary, start_run  
)

from db.exceptions import BusinessException, ApplicationException

def process_invoice(invoice_number: str, group_number: str | None) -> None:  
    """Your actual automation goes here."""  
    pass


def main(csv_path: str, retry_failed_only: bool = False) -> None:  
    file_name = Path(csv_path).name

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
        run = session.get(Run, run_id)
        if not run:
            raise ApplicationException(f"Run {run_id} not found")
        run.total_records = len(work)

    # ── Transactions: one per invoice ──────────────────────  
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

    except BaseException as e:  
        fatal = f"{type(e).__name__}: {e}"  
        raise  
    finally:  
        # ── Final transaction: always close the run ─────────────  
        with session_scope() as session:  
            complete_run(session, run_id, failure_reason=fatal) 
            print(run_summary(session, run_id))  
            
if __name__ == "__main__":
    file_path = '//NASDATA201/SHAREDATA/MV-RCR01/SHARED/RC Experience/DO NOT REMOVE - HCx Ontario Reports'
    today = datetime.today().strftime('%Y%m%d')
    
    file_name = f'{today}_PAANS_BOT_v2.csv'
    csv_path = f'{file_path}/{file_name}'
    main(csv_path)