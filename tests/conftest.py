import csv
import io
from datetime import datetime, timedelta
from pathlib import Path

import pytest  
from sqlalchemy import create_engine, event, insert  
from sqlalchemy.orm import sessionmaker  
from sqlalchemy.pool import StaticPool

import db.base as db_base  
from db import repository  
from db.base import Base  
from db.models import ExceptionType, ItemStatus


@pytest.fixture  
def engine():  
    """Fresh in-memory DB per test, with FK enforcement on."""  
    eng = create_engine(  
        "sqlite://",  
        connect_args={"check_same_thread": False},  
        poolclass=StaticPool,  
    )

    @event.listens_for(eng, "connect")  
    def _enable_fks(dbapi_conn, _record):  
        cur = dbapi_conn.cursor()  
        cur.execute("PRAGMA foreign_keys=ON")  
        cur.close()

    Base.metadata.create_all(eng)  
    yield eng  
    eng.dispose()


@pytest.fixture  
def Session(engine):  
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture  
def session(Session):  
    """Single session for unit tests. Rolled back on teardown."""  
    s = Session()  
    yield s  
    s.rollback()  
    s.close()


@pytest.fixture  
def patched_db(monkeypatch, Session):  
    """Point db.base.session_scope at the in-memory DB.

    session_scope() looks up SessionLocal as a module global at call time, so  
    patching db.base.SessionLocal reaches main.py even though main imported  
    session_scope by reference.  
    """  
    monkeypatch.setattr(db_base, "SessionLocal", Session)  
    return Session


@pytest.fixture
def make_csv(monkeypatch):
    """Create CSVs in memory and expose them as pseudo-Path objects.

    The repository reads via Path.open(), so we patch Path.open to return
    StringIO content for fixture-generated pseudo paths.
    """
    registry: dict[str, str] = {}
    sentinel = "__inmem__"
    original_open = Path.open

    def _path_open(self: Path, *args, **kwargs):
        key = str(self)
        if key in registry:
            return io.StringIO(registry[key])
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", _path_open)

    def _make(name, rows, *, header=("HCENPTACCT", "ZZACPAANSGROUP"), bom=False):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        if header:
            writer.writerow(header)
        writer.writerows(rows)
        csv_text = buffer.getvalue()
        if bom:
            csv_text = "\ufeff" + csv_text

        pseudo_path = Path(f"{sentinel}/{name}")
        registry[str(pseudo_path)] = csv_text
        return pseudo_path

    return _make


class Clock:  
    def __init__(self, start: datetime):  
        self.t = start

    def __call__(self) -> datetime:  
        return self.t

    def advance(self, **kwargs) -> datetime:  
        self.t += timedelta(**kwargs)  
        return self.t


@pytest.fixture  
def clock(monkeypatch):  
    """Freeze repository.now().

    Caveat: column defaults (created_at, loaded_at, updated_at) captured the  
    real `now` function object at class-definition time, so they keep using  
    wall clock. Only timestamps the repository sets explicitly are frozen.  
    """  
    c = Clock(datetime(2026, 11, 16, 9, 0, 0))  
    monkeypatch.setattr(repository, "now", c)  
    return c


# ---------- helpers ----------

def seed(session, file_name: str, invoices, *, run=None):  
    """Create a run and register input rows without touching the filesystem."""  
    from db.models import Input  
    run = run or repository.create_run(session, file_name)  
    session.execute(  
        insert(Input),  
        [  
            {  
                "file_name": file_name,  
                "invoice_number": inv,  
                "group_number": "G1",  
                "row_number": i,  
                "loaded_by_run_id": run.run_id,  
            }  
            for i, inv in enumerate(invoices, start=1)  
        ],  
    )  
    session.flush()  
    return run


def attempt(session, run, invoice, status=ItemStatus.SUCCESS, **kwargs):  
    return repository.record_attempt(  
        session,  
        run_id=run.run_id,  
        invoice_number=invoice,  
        status=status,  
        start_time=repository.now(),  
        **kwargs,  
    )


def fail(session, run, invoice, kind=ExceptionType.BUSINESS, reason="nope"):  
    return attempt(  
        session, run, invoice,  
        status=ItemStatus.FAILED,  
        exception_type=kind,  
        exception_reason=reason,  
    )  