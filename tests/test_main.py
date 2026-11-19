from types import SimpleNamespace

import pytest
from sqlalchemy import select

import main as app_main
from db.exceptions import ApplicationException, BusinessException
from db.models import Attempt, ExceptionType, ItemStatus, Run, RunStatus
from db.repository import WorkItem


class DummyIDXClient:
	def __init__(self, username: str, password: str):
		self.username = username
		self.password = password
		self.login_page = SimpleNamespace(login=lambda: None)
		self.settings_page = SimpleNamespace(change_group=lambda _n: None, logout=lambda: None)
		self.vtb_page = SimpleNamespace(select_vtb_option=lambda _name: None)


@pytest.mark.parametrize("bad_date", ["", "2026-11-16", "202611", "abcdefgh", "20261301"])
def test_main_rejects_invalid_file_date(monkeypatch, bad_date):
	monkeypatch.setattr(app_main, "load_dotenv", lambda: None)
	with pytest.raises(ValueError, match="YYYYMMDD"):
		app_main.main(bad_date)


def test_main_records_success_and_all_failure_types(monkeypatch, patched_db):
	monkeypatch.setenv("IDX_USERNAME", "user")
	monkeypatch.setenv("IDX_PASSWORD", "pass")
	monkeypatch.setattr(app_main, "load_dotenv", lambda: None)
	monkeypatch.setattr(app_main.os.path, "exists", lambda _p: True)
	monkeypatch.setattr(app_main, "tqdm", lambda items: items)
	monkeypatch.setattr(app_main, "IDXClient", DummyIDXClient)

	work = [
		WorkItem("INV_OK", "G1"),
		WorkItem("INV_BIZ", "G1"),
		WorkItem("INV_APP", "G1"),
		WorkItem("INV_PY", "G1"),
	]

	monkeypatch.setattr(app_main, "register_input_file", lambda *_args, **_kwargs: len(work))
	monkeypatch.setattr(app_main, "get_work_items", lambda *_args, **_kwargs: work)

	reset_calls = []
	monkeypatch.setattr(app_main, "reset", lambda idx_client: reset_calls.append(idx_client))

	def fake_process(_client, invoice_number, _group):
		if invoice_number == "INV_BIZ":
			raise BusinessException("business fail")
		if invoice_number == "INV_APP":
			raise ApplicationException("app fail")
		if invoice_number == "INV_PY":
			raise RuntimeError("python fail")

	monkeypatch.setattr(app_main, "process_invoice", fake_process)

	app_main.main("20261116", retry_failed_only=False)

	Session = patched_db
	session = Session()
	try:
		run = session.scalars(select(Run)).one()
		assert run.status is RunStatus.COMPLETED
		assert run.total_records == 4

		attempts = {
			a.invoice_number: a
			for a in session.scalars(select(Attempt)).all()
		}
		assert attempts["INV_OK"].status is ItemStatus.SUCCESS

		assert attempts["INV_BIZ"].status is ItemStatus.FAILED
		assert attempts["INV_BIZ"].exception_type is ExceptionType.BUSINESS

		assert attempts["INV_APP"].status is ItemStatus.FAILED
		assert attempts["INV_APP"].exception_type is ExceptionType.APPLICATION

		assert attempts["INV_PY"].status is ItemStatus.FAILED
		assert attempts["INV_PY"].exception_type is ExceptionType.PYTHON
	finally:
		session.close()

	assert len(reset_calls) == 1


def test_main_marks_run_failed_when_fatal_error_occurs(monkeypatch, patched_db):
	monkeypatch.setenv("IDX_USERNAME", "user")
	monkeypatch.setenv("IDX_PASSWORD", "pass")
	monkeypatch.setattr(app_main, "load_dotenv", lambda: None)
	monkeypatch.setattr(app_main.os.path, "exists", lambda _p: True)
	monkeypatch.setattr(app_main, "tqdm", lambda items: items)

	monkeypatch.setattr(app_main, "register_input_file", lambda *_args, **_kwargs: 1)
	monkeypatch.setattr(
		app_main,
		"get_work_items",
		lambda *_args, **_kwargs: [WorkItem("INV1", "G1")],
	)

	class BrokenIDXClient:
		def __init__(self, *_args, **_kwargs):
			raise RuntimeError("browser not available")

	monkeypatch.setattr(app_main, "IDXClient", BrokenIDXClient)

	with pytest.raises(RuntimeError, match="browser not available"):
		app_main.main("20261116", retry_failed_only=False)

	Session = patched_db
	session = Session()
	try:
		run = session.scalars(select(Run)).one()
		assert run.status is RunStatus.FAILED
		assert run.failure_reason is not None
		assert "RuntimeError: browser not available" in run.failure_reason
	finally:
		session.close()
