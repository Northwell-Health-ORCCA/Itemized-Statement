import csv  
from datetime import datetime  
from pathlib import Path

from sqlalchemy import func, insert, select

from .models import (  
    Attempt, ExceptionType, Input, ItemStatus, Output, Run, RunStatus, utcnow  
)


# ---------- Run lifecycle ----------

def load_input_file(session, csv_path: str | Path) -> Run:  
    """Read the CSV, create a Run, and bulk-insert the raw rows into `inputs`."""  
    csv_path = Path(csv_path)  
    run = Run(file_name=csv_path.name, status=RunStatus.LOADED)  
    session.add(run)  
    session.flush()  # populates run.run_id

    rows = []  
    with csv_path.open(newline="", encoding="utf-8-sig") as f:  
        reader = csv.DictReader(f)  
        for i, row in enumerate(reader, start=1):  
            invoice = (row.get("HCENPTACCT") or "").strip()  
            if not invoice:  
                continue  # skip blank lines  
            rows.append({  
                "run_id": run.run_id,  
                "file_name": csv_path.name,  
                "invoice_number": invoice,  
                "group_number": (row.get("ZZACPAANSGROUP") or "").strip() or None,  
                "row_number": i,  
            })

    if rows:  
        session.execute(insert(Input), rows)

    run.total_records = len(rows)  
    return run


def start_run(run: Run) -> Run:  
    run.status = RunStatus.IN_PROCESS  
    run.start_time = utcnow()  
    return run


def complete_run(run: Run, failure_reason: str | None = None) -> Run:  
    run.end_time = utcnow()  
    run.status = RunStatus.FAILED if failure_reason else RunStatus.COMPLETED  
    run.failure_reason = failure_reason  
    return run


def get_work_items(session, run: Run) -> list[Input]:  
    """Rows to process for this run, de-duplicated by invoice."""  
    min_id_per_invoice = (  
        select(func.min(Input.id).label("min_id"))  
        .where(Input.run_id == run.run_id)  
        .group_by(Input.invoice_number)  
    )

    stmt = (  
        select(Input)  
        .where(Input.id.in_(min_id_per_invoice))  
        .order_by(Input.row_number)  
    )  
    return list(session.scalars(stmt))


# ---------- record an attempt + sync the output ----------

def record_attempt(  
    session,  
    *,  
    run: Run,  
    invoice_number: str,  
    file_name: str,  
    status: ItemStatus,  
    start_time: datetime,  
    end_time: datetime | None = None,  
    exception_type: ExceptionType | None = None,  
    exception_reason: str | None = None,  
    group_number: str | None = None,  
) -> Attempt:  
    """  
    Writes one immutable row to `attempts` AND upserts the matching row in  
    `outputs` so outputs always reflects the latest attempt.  
    Both happen in the caller's transaction — all or nothing.  
    """  
    end_time = end_time or utcnow()

    output = session.get(Output, invoice_number)  
    if output is None:  
        # First time this invoice has EVER been seen  
        output = Output(  
            invoice_number=invoice_number,  
            first_file_name=file_name,  
            first_run_id=run.run_id,  
            attempt_count=0,  
        )  
        session.add(output)  
        session.flush()

    attempt_number = output.attempt_count + 1

    attempt = Attempt(  
        invoice_number=invoice_number,  
        attempt_number=attempt_number,  
        file_name=file_name,  
        run_id=run.run_id,  
        group_number=group_number,  
        status=status,  
        exception_type=exception_type,  
        exception_reason=exception_reason,  
        start_time=start_time,  
        end_time=end_time,  
    )  
    session.add(attempt)

    # Overwrite the "latest" snapshot. first_file_name / first_run_id untouched.  
    output.attempt_count = attempt_number  
    output.status = status  
    output.exception_type = exception_type  
    output.exception_reason = exception_reason  
    output.start_time = start_time  
    output.end_time = end_time  
    output.run_id = run.run_id  
    if group_number:  
        output.group_number = group_number

    session.flush()  
    return attempt  