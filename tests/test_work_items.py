import pytest

from db import repository
from db.models import Input, Output, ItemStatus


def _add_input(session, run, invoice: str, row_number: int, group: str = "G1") -> None:
	session.add(
		Input(
			run_id=run.run_id,
			file_name=run.file_name,
			invoice_number=invoice,
			group_number=group,
			row_number=row_number,
		)
	)


def _add_output(session, invoice: str, *, run, status: ItemStatus) -> None:
	session.add(
		Output(
			invoice_number=invoice,
			first_file_name=run.file_name,
			first_run_id=run.run_id,
			status=status,
			run_id=run.run_id,
			attempt_count=1,
		)
	)


def test_get_work_items_default_returns_failed_and_staged_not_success(session):
	run = repository.create_run(session, "work.csv")
	_add_input(session, run, "INV1", 1)
	_add_input(session, run, "INV2", 2)
	_add_input(session, run, "INV3", 3)

	_add_output(session, "INV1", run=run, status=ItemStatus.SUCCESS)
	_add_output(session, "INV2", run=run, status=ItemStatus.FAILED)
	_add_output(session, "INV3", run=run, status=ItemStatus.STAGED)
	session.flush()

	work = repository.get_work_items(session, run.run_id)
	assert [w.invoice_number for w in work] == ["INV2", "INV3"]


def test_get_work_items_retry_false_includes_never_attempted(session):
	run = repository.create_run(session, "work2.csv")
	_add_input(session, run, "INV10", 1)
	_add_input(session, run, "INV11", 2)

	_add_output(session, "INV10", run=run, status=ItemStatus.FAILED)
	session.flush()

	work = repository.get_work_items(session, run.run_id, retry_failed_only=False)
	assert [w.invoice_number for w in work] == ["INV10", "INV11"]


def test_get_work_items_raises_for_unknown_run(session):
	with pytest.raises(ValueError, match="No such run"):
		repository.get_work_items(session, "20000101_000000")
