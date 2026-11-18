from sqlalchemy import select

from db import repository
from db.models import Attempt, Input, ItemStatus


def test_register_input_file_inserts_rows_with_run_id_and_normalized_group(session, make_csv):
	csv_path = make_csv(
		"input_a.csv",
		[
			["A100", "G1"],
			["", "G2"],
			["A200", "   "],
		],
	)
	run = repository.create_run(session, csv_path.name)

	loaded = repository.register_input_file(session, csv_path, run.run_id)
	assert loaded == 2

	rows = session.scalars(
		select(Input).order_by(Input.row_number)
	).all()
	assert [r.invoice_number for r in rows] == ["A100", "A200"]
	assert all(r.run_id == run.run_id for r in rows)
	assert rows[0].group_number == "G1"
	assert rows[1].group_number is None


def test_register_input_file_dedupes_existing_invoices_for_same_file(session, make_csv):
	csv_path = make_csv(
		"input_b.csv",
		[
			["INV-1", "G1"],
			["INV-2", "G2"],
		],
	)
	run1 = repository.create_run(session, csv_path.name)
	run2 = repository.create_run(session, csv_path.name)

	first_load = repository.register_input_file(session, csv_path, run1.run_id)
	assert first_load == 2

	csv_path = make_csv(
		"input_b.csv",
		[
			["INV-2", "G2"],
			["INV-3", "G3"],
		],
	)
	second_load = repository.register_input_file(session, csv_path, run2.run_id)
	assert second_load == 1

	invoices = session.scalars(
		select(Input.invoice_number).where(Input.file_name == "input_b.csv").order_by(Input.id)
	).all()
	assert invoices == ["INV-1", "INV-2", "INV-3"]

	staged = session.scalars(select(Attempt).order_by(Attempt.attempt_id)).all()
	assert len(staged) == 3
	assert all(a.status is ItemStatus.STAGED for a in staged)
