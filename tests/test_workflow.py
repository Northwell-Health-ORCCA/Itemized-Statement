from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

from workflow import process_invoice, reset


def _make_client():
    return SimpleNamespace(
        login_page=SimpleNamespace(login=Mock()),
        settings_page=SimpleNamespace(logout=Mock(), change_group=Mock()),
        vtb_page=SimpleNamespace(select_vtb_option=Mock()),
        patient_services=SimpleNamespace(
            navigate_to_patient_inquiry=Mock(),
            invoice_list=SimpleNamespace(navigate_to_demand_statement=Mock()),
            demand_statement=SimpleNamespace(demand_statement=Mock()),
            select_invoices=SimpleNamespace(search_for_invoice=Mock()),
            device_selection=SimpleNamespace(select_device=Mock()),
        ),
    )


def test_reset_reinitializes_idx_session():
    client = _make_client()

    reset(cast(Any, client))

    client.settings_page.logout.assert_called_once_with()
    client.login_page.login.assert_called_once_with()
    client.settings_page.change_group.assert_called_once_with(2)
    client.vtb_page.select_vtb_option.assert_called_once_with("Patient Services")


def test_process_invoice_strips_p_prefix_and_uses_given_group():
    client = _make_client()

    process_invoice(cast(Any, client), "P123456", "2")

    client.patient_services.navigate_to_patient_inquiry.assert_called_once_with("123456", "2")
    client.patient_services.invoice_list.navigate_to_demand_statement.assert_called_once_with()
    client.patient_services.demand_statement.demand_statement.assert_called_once_with()
    client.patient_services.select_invoices.search_for_invoice.assert_called_once_with("123456")
    client.patient_services.device_selection.select_device.assert_called_once_with()
    client.vtb_page.select_vtb_option.assert_called_once_with("Patient Services")


def test_process_invoice_uses_default_group_when_missing_or_blank():
    client_none = _make_client()
    process_invoice(cast(Any, client_none), "12345", None)
    client_none.patient_services.navigate_to_patient_inquiry.assert_called_once_with("12345", "3")

    client_blank = _make_client()
    process_invoice(cast(Any, client_blank), "12345", "   ")
    client_blank.patient_services.navigate_to_patient_inquiry.assert_called_once_with("12345", "3")
