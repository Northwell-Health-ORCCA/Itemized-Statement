import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import NamedTuple

from sqlalchemy import func, insert, select
from sqlalchemy.orm import aliased

from .models import (
    Attempt,
    ExceptionType,
    Input,
    ItemStatus,
    Output,
    Run,
    RunStatus,
    now,
)


class WorkItem(NamedTuple):  
    """Plain data — safe to carry across session boundaries."""  
    invoice_number: str  
    group_number: str | None


# ---------- Run lifecycle ----------

def make_run_id(session, when: datetime | None = None) -> str:  
    """YYYYMMDD_HHMMSS, with _2, _3... suffixes if that second is taken."""  
    when = when or now()  
    base = when.strftime("%Y%m%d_%H%M%S")  
    candidate, n = base, 1  
    while session.get(Run, candidate) is not None:  
        n += 1  
        candidate = f"{base}_{n}"  
    return candidate


def create_run(session, file_name: str) -> Run:  
    """New run against a file."""  
    run = Run(  
        run_id=make_run_id(session),  
        file_name=file_name,  
        status=RunStatus.LOADED,  
    )  
    session.add(run)  
    session.flush()  
    return run


def start_run(session, run_id: str) -> Run:  
    run = session.get(Run, run_id)  
    if run is None:  
        raise ValueError(f"No such run: {run_id}")  
    run.status = RunStatus.IN_PROCESS  
    run.start_time = now()  
    session.flush()  
    return run


def complete_run(session, run_id: str, failure_reason: str | None = None) -> Run:  
    run = session.get(Run, run_id)  
    if run is None:  
        raise ValueError(f"No such run: {run_id}")  
    run.end_time = now()  
    run.status = RunStatus.FAILED if failure_reason else RunStatus.COMPLETED  
    run.failure_reason = failure_reason  
    session.flush()  
    return run

def close_stale_runs(session, max_age_hours: int = 12) -> int:  
    cutoff = now() - timedelta(hours=max_age_hours)  
    stale = session.scalars(  
        select(Run).where(  
            Run.status == RunStatus.IN_PROCESS,  
            Run.start_time < cutoff,  
        )  
    ).all()  
    for run in stale:  
        run.status = RunStatus.FAILED  
        run.end_time = now()  
        run.failure_reason = "Abandoned — no completion recorded (process killed?)"  
    return len(stale)  

# ---------- Input loading ----------

def register_input_file(session, csv_path: str | Path, run_id: str) -> int:  
    """Insert the file's rows into `inputs`. Skips invoices already recorded  
    for this file name, so re-running a file is a no-op here."""  
    csv_path = Path(csv_path)  
    existing = set(session.scalars(  
        select(Input.invoice_number).where(Input.file_name == csv_path.name)  
    ))

    rows = []  
    with csv_path.open(newline="", encoding="utf-8-sig") as f:  
        for i, row in enumerate(csv.DictReader(f), start=1):  
            invoice = (row.get("HCENPTACCT") or "").strip()  
            if not invoice or invoice in existing:  
                continue  
            existing.add(invoice)  # dedupe within the file too  
            rows.append({  
                "file_name": csv_path.name,  
                "invoice_number": invoice,  
                "group_number": (row.get("ZZACPAANSGROUP") or "").strip() or None,  
                "row_number": i,  
                "run_id": run_id,  
            })

    if rows:  
        session.execute(insert(Input), rows)
        session.commit()
        for row in rows:
            record_attempt(session, run_id=run_id, invoice_number=row["invoice_number"], group_number=row["group_number"], start_time=now())
    return len(rows)


# ---------- Work selection ----------

def get_work_items(  
    session, run_id: str, *, retry_failed_only: bool = True  
) -> list[WorkItem]:  
    """Invoices from this run's file still needing work.

    Always skips invoices that have already SUCCEEDED anywhere — success is  
    permanent. retry_failed_only=True also skips never-attempted invoices.  
    """  
    run = session.get(Run, run_id)  
    if run is None:  
        raise ValueError(f"No such run: {run_id}")

    succeeded = select(Output.invoice_number).where(Output.status == ItemStatus.SUCCESS)

    stmt = (  
        select(Input.invoice_number, Input.group_number)  
        .where(Input.file_name == run.file_name)  
        .where(Input.invoice_number.not_in(succeeded))  
        .order_by(Input.row_number)  
    )

    if retry_failed_only:  
        failed = select(Output.invoice_number).where(Output.status.in_([ItemStatus.FAILED,ItemStatus.STAGED]))  
        stmt = stmt.where(Input.invoice_number.in_(failed))

    return [WorkItem(inv, grp) for inv, grp in session.execute(stmt)]


# ---------- The core write ----------

def record_attempt(  
    session,  
    *,  
    run_id: str,  
    invoice_number: str,  
    start_time: datetime,  
    status: ItemStatus = ItemStatus.STAGED,  
    end_time: datetime | None = None,  
    exception_type: ExceptionType | None = None,  
    exception_reason: str | None = None,  
    group_number: str | None = None,  
) -> Attempt:  
    """Upsert into `attempts` by (invoice_number, run_id) and sync `outputs` in one transaction.  
    The only place either table is written."""  
    run = session.get(Run, run_id)  
    if run is None:  
        raise ValueError(f"No such run: {run_id}")  
    end_time = end_time or now()

    output = session.get(Output, invoice_number)  
    if output is None:  
        # First file this invoice ever appeared on — from inputs, not attempts  
        first = session.execute(  
            select(Input.file_name, Input.loaded_at, Input.run_id)  
            .where(Input.invoice_number == invoice_number)  
            .order_by(Input.loaded_at, Input.id)  
            .limit(1)  
        ).first()          
        output = Output(  
            invoice_number=invoice_number,  
            first_file_name=first.file_name if first else run.file_name,  
            first_run_id=first.run_id if first else run.run_id,
            first_seen_at=first.loaded_at if first else now(),  
            attempt_count=0,  
        )  
        session.add(output)  
        session.flush()

    attempt = session.execute(
        select(Attempt)
        .where(
            Attempt.invoice_number == invoice_number,
            Attempt.run_id == run.run_id
        )
        .limit(1)
    ).scalar_one_or_none()

    if attempt is None:
        n = output.attempt_count + 1
        attempt = Attempt(  
            invoice_number=invoice_number,  
            attempt_number=n,  
            file_name=run.file_name,  
            run_id=run.run_id,  
            group_number=group_number,  
            status=status,  
            exception_type=exception_type,  
            exception_reason=exception_reason,  
            start_time=start_time,  
            end_time=end_time,  
        )
        session.add(attempt)
        output.attempt_count = n
    else:
        attempt.file_name = run.file_name
        attempt.group_number = group_number
        attempt.status = status
        attempt.exception_type = exception_type
        attempt.exception_reason = exception_reason
        attempt.start_time = start_time
        attempt.end_time = end_time
        
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


# ---------- Reporting / integrity ----------

def run_summary(session, run_id: str) -> dict[str, int]:  
    rows = session.execute(  
        select(Attempt.status, func.count())  
        .where(Attempt.run_id == run_id)  
        .group_by(Attempt.status)  
    )  
    return {status.value: count for status, count in rows}


def reconcile(session) -> list[dict]:  
    """Rows where `outputs` disagrees with the latest row in `attempts`.  
    Should always return []."""  
    rn = func.row_number().over(  
        partition_by=Attempt.invoice_number,  
        order_by=Attempt.attempt_number.desc(),  
    ).label("rn")

    latest = select(Attempt, rn).subquery()  
    L = aliased(Attempt, latest)

    stmt = (  
        select(  
            Output.invoice_number,  
            Output.status.label("output_status"),  
            L.status.label("attempt_status"),  
            Output.run_id.label("output_run"),  
            L.run_id.label("attempt_run"),  
            Output.attempt_count,  
            L.attempt_number,  
        )  
        .join(L, L.invoice_number == Output.invoice_number)  
        .where(latest.c.rn == 1)  
        .where(  
            (Output.status.is_distinct_from(L.status))  
            | (Output.run_id.is_distinct_from(L.run_id))  
            | (Output.attempt_count != L.attempt_number)  
        )  
    )  
    return [dict(r._mapping) for r in session.execute(stmt)]  