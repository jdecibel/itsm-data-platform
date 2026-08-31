"""
Pure logic, no Airflow needed — runs anywhere: `pytest tests/test_tables.py`
"""
from itsm_common.tables import TABLES

EXPECTED_NAMES = {
    "staff", "clients", "assets", "incidents",
    "projects", "timesheets", "invoices", "helpdesk_tickets",
}


def test_eight_tables_defined():
    assert len(TABLES) == 8


def test_table_names_are_unique():
    names = [t.name for t in TABLES]
    assert len(names) == len(set(names))


def test_every_table_has_columns():
    for t in TABLES:
        assert len(t.columns) > 0, f"{t.name} has no columns defined"


def test_expected_table_names_present():
    assert {t.name for t in TABLES} == EXPECTED_NAMES
