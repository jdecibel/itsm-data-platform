"""
Pure logic, no Airflow needed — runs anywhere: `pytest tests/test_s3_keys.py`
"""
from itsm_common.s3_keys import s3_key_for


def test_format_matches_convention():
    assert s3_key_for("staff", "2026-01-15") == "staff/dt=2026-01-15/staff_20260115.csv"


def test_different_tables_get_different_prefixes():
    a = s3_key_for("staff", "2026-01-15")
    b = s3_key_for("clients", "2026-01-15")
    assert a.split("/")[0] != b.split("/")[0]


def test_same_table_different_dates_get_different_keys():
    a = s3_key_for("staff", "2026-01-15")
    b = s3_key_for("staff", "2026-01-16")
    assert a != b


def test_same_table_same_date_is_deterministic():
    # Idempotency depends on this: re-running the same logical date must
    # produce the exact same key so replace=True overwrites instead of
    # creating a second object.
    assert s3_key_for("staff", "2026-01-15") == s3_key_for("staff", "2026-01-15")
