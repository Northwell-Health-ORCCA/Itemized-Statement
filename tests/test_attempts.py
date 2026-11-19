from datetime import datetime

import pytest
from sqlalchemy import select

from db import repository
from db.models import ExceptionType, Input, ItemStatus, Output


def _seed_input(session, run, invoice: str, *, group: str = "G1") -> None:
	session.add(
		Input(
			run_id=run.run_id,
			file_name=run.file_name,
			invoice_number=invoice,
			group_number=group,
			row_number=1,
		)
	)
	session.flush()


def test_record_attempt_creates_output_with_first_seen_provenance(session):
	run = repository.create_run(session, "attempts.csv")
	_seed_input(session, run, "INV100")

	started = datetime(2026, 11, 16, 9, 0, 0)
	ended = datetime(2026, 11, 16, 9, 1, 0)
	attempt = repository.record_attempt(
		session,
		run_id=run.run_id,
		invoice_number="INV100",
		group_number="G1",
		start_time=started,
		end_time=ended,
		status=ItemStatus.SUCCESS,
	)

	assert attempt.attempt_number == 1
	output = session.get(Output, "INV100")
	assert output is not None
	assert output.first_file_name == run.file_name
	assert output.first_run_id == run.run_id
	assert output.attempt_count == 1
	assert output.status is ItemStatus.SUCCESS
	assert output.group_number == "G1"


def test_record_attempt_overwrites_same_run_attempt_and_updates_output(session):
	run = repository.create_run(session, "retry.csv")
	_seed_input(session, run, "INV200")

	a1 = repository.record_attempt(
		session,
		run_id=run.run_id,
		invoice_number="INV200",
		group_number="G1",
		start_time=datetime(2026, 11, 16, 10, 0, 0),
		status=ItemStatus.FAILED,
		exception_type=ExceptionType.BUSINESS,
		exception_reason="first fail",
	)
	a2 = repository.record_attempt(
		session,
		run_id=run.run_id,
		invoice_number="INV200",
		group_number="G2",
		start_time=datetime(2026, 11, 16, 10, 5, 0),
		status=ItemStatus.SUCCESS,
	)

	assert (a1.attempt_number, a2.attempt_number) == (1, 1)

	output = session.get(Output, "INV200")
	assert output.attempt_count == 1
	assert output.status is ItemStatus.SUCCESS
	assert output.exception_type is None
	assert output.exception_reason is None
	assert output.group_number == "G2"

	attempts = session.scalars(
		select(repository.Attempt).where(repository.Attempt.invoice_number == "INV200").order_by(repository.Attempt.attempt_number)
	).all()
	assert len(attempts) == 1
	assert attempts[0].attempt_number == 1
	assert attempts[0].status is ItemStatus.SUCCESS
	assert attempts[0].group_number == "G2"


def test_record_attempt_raises_for_unknown_run_id(session):
	with pytest.raises(ValueError, match="No such run"):
		repository.record_attempt(
			session,
			run_id="missing_run",
			invoice_number="INV404",
			start_time=datetime(2026, 11, 16, 10, 0, 0),
		)
