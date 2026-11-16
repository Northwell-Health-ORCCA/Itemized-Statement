import re  
from datetime import datetime, timedelta

import pytest

from db import repository  
from db.models import Run, RunStatus, now


def test_create_run_defaults(session):  
    run = repository.create_run(session, "file_a.csv")  
    assert re.fullmatch(r"\d{8}_\d{6}", run.run_id)  
    assert run.status is RunStatus.LOADED  
    assert run.start_time is None  
    assert run.end_time is None


def test_run_id_increments_per_file(session):  
    a1 = repository.create_run(session, "a.csv")  
    a2 = repository.create_run(session, "a.csv")  
    a3 = repository.create_run(session, "a.csv")  
    b1 = repository.create_run(session, "b.csv")  
    assert re.fullmatch(r"\d{8}_\d{6}", a1.run_id)
    assert a2.run_id == f"{a1.run_id}_2"
    assert a3.run_id == f"{a1.run_id}_3"
    assert b1.run_id != a1.run_id


def test_make_run_id_suffixes_on_collision(session):  
    when = datetime(2026, 11, 16, 9, 15, 0)

    first = repository.make_run_id(session, when)  
    assert first == "20261116_091500"  
    session.add(Run(run_id=first, file_name="a.csv"))  
    session.flush()

    second = repository.make_run_id(session, when)  
    assert second == "20261116_091500_2"  
    session.add(Run(run_id=second, file_name="a.csv"))  
    session.flush()

    assert repository.make_run_id(session, when) == "20261116_091500_3"


def test_suffixed_run_id_fits_column(session):  
    when = datetime(2026, 11, 16, 9, 15, 0)  
    rid = repository.make_run_id(session, when) + "_10"  
    assert len(rid) <= 20


def test_start_run(session, clock):  
    run = repository.create_run(session, "a.csv")  
    repository.start_run(session, run.run_id)  
    assert run.status is RunStatus.IN_PROCESS  
    assert run.start_time == clock.t


def test_complete_run_success(session, clock):  
    run = repository.create_run(session, "a.csv")  
    repository.start_run(session, run.run_id)  
    clock.advance(minutes=5)  
    repository.complete_run(session, run.run_id)  
    assert run.status is RunStatus.COMPLETED  
    assert run.failure_reason is None  
    assert run.start_time is not None  
    assert run.end_time is not None  
    assert (run.end_time - run.start_time) == timedelta(minutes=5)


def test_complete_run_with_failure(session):  
    run = repository.create_run(session, "a.csv")  
    repository.start_run(session, run.run_id)  
    repository.complete_run(session, run.run_id, failure_reason="SAP unavailable")  
    assert run.status is RunStatus.FAILED  
    assert run.failure_reason == "SAP unavailable"  
    assert run.end_time is not None


@pytest.mark.parametrize("fn", [  
    repository.start_run,  
    repository.complete_run,  
    repository.get_work_items,  
])  
def test_unknown_run_id_raises(session, fn):  
    with pytest.raises(ValueError, match="No such run"):  
        fn(session, "20000101_000000")


def test_close_stale_runs_marks_abandoned(session):  
    run = repository.create_run(session, "a.csv")  
    repository.start_run(session, run.run_id)  
    run.start_time = now() - timedelta(hours=24)  
    session.flush()

    assert repository.close_stale_runs(session, max_age_hours=12) == 1  
    assert run.status is RunStatus.FAILED
    assert run.failure_reason is not None
    assert "Abandoned" in run.failure_reason  
    assert run.end_time is not None


def test_close_stale_runs_leaves_recent_alone(session):  
    run = repository.create_run(session, "a.csv")  
    repository.start_run(session, run.run_id)  
    assert repository.close_stale_runs(session, max_age_hours=12) == 0  
    assert run.status is RunStatus.IN_PROCESS


def test_close_stale_runs_ignores_loaded_and_completed(session):  
    loaded = repository.create_run(session, "a.csv")           # start_time is NULL  
    done = repository.create_run(session, "b.csv")  
    repository.start_run(session, done.run_id)  
    done.start_time = now() - timedelta(days=3)  
    repository.complete_run(session, done.run_id)  
    session.flush()

    assert repository.close_stale_runs(session, max_age_hours=1) == 0  
    assert loaded.status is RunStatus.LOADED  
    assert done.status is RunStatus.COMPLETED  