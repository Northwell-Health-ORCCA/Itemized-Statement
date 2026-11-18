from datetime import datetime

from db import repository
from db.models import Input, ItemStatus, Output


def _seed_invoice(session, run, invoice: str) -> None:
	session.add(
		Input(
			run_id=run.run_id,
			file_name=run.file_name,
			invoice_number=invoice,
			group_number="G1",
			row_number=1,
		)
	)
	session.flush()


def test_reconcile_returns_empty_when_latest_attempt_matches_output(session):
	run = repository.create_run(session, "integrity.csv")
	_seed_invoice(session, run, "INV300")

	repository.record_attempt(
		session,
		run_id=run.run_id,
		invoice_number="INV300",
		start_time=datetime(2026, 11, 16, 11, 0, 0),
		status=ItemStatus.FAILED,
	)
	repository.record_attempt(
		session,
		run_id=run.run_id,
		invoice_number="INV300",
		start_time=datetime(2026, 11, 16, 11, 5, 0),
		status=ItemStatus.SUCCESS,
	)

	assert repository.reconcile(session) == []


def test_reconcile_reports_rows_when_output_is_tampered(session):
	run = repository.create_run(session, "integrity2.csv")
	_seed_invoice(session, run, "INV301")

	repository.record_attempt(
		session,
		run_id=run.run_id,
		invoice_number="INV301",
		start_time=datetime(2026, 11, 16, 12, 0, 0),
		status=ItemStatus.SUCCESS,
	)

	out = session.get(Output, "INV301")
	out.status = ItemStatus.FAILED
	out.attempt_count = 99
	session.flush()

	drift = repository.reconcile(session)
	assert len(drift) == 1
	assert drift[0]["invoice_number"] == "INV301"
	assert drift[0]["output_status"] == ItemStatus.FAILED
	assert drift[0]["attempt_status"] == ItemStatus.SUCCESS
