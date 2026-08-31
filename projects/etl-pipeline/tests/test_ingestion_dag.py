"""
Tests for the real extract/load task logic in itsm_raw_ingestion.py.

Needs apache-airflow + providers installed, so this file skips itself if
`airflow` isn't importable — run it inside the Airflow container, not the
bare host:
    docker compose exec airflow-scheduler sh -c "pip install -q pytest && pytest /opt/airflow/tests/test_ingestion_dag.py"

Hooks (S3Hook/PostgresHook) are mocked — these don't touch a live
LocalStack/Postgres, they pin the *ordering* guarantee that isn't visible
just from reading the code once.
"""
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("airflow")

from itsm_common.tables import TableConfig

STAFF = TableConfig("staff", ["staff_id", "name", "role"])


def _fake_cursor_and_conn():
    fake_cursor = MagicMock()
    fake_cursor.__enter__.return_value = fake_cursor
    fake_cursor.__exit__.return_value = False

    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
    return fake_cursor, fake_conn


def test_load_to_postgres_copies_before_truncating_before_inserting():
    from itsm_raw_ingestion import _load_to_postgres

    fake_cursor, fake_conn = _fake_cursor_and_conn()

    with patch("itsm_raw_ingestion.S3Hook") as mock_s3hook, \
         patch("itsm_raw_ingestion.PostgresHook") as mock_pghook, \
         patch("psycopg2.sql.Composed.as_string", return_value="COPY staging (...) FROM STDIN ..."):
        mock_s3hook.return_value.read_key.return_value = "staff_id,name,role\nEMP-00001,Ann,Employee\n"
        mock_pghook.return_value.get_conn.return_value = fake_conn

        _load_to_postgres(STAFF, ds="2026-01-15")

    call_order = [name for name, args, kwargs in fake_cursor.method_calls]
    # CREATE TEMP TABLE (execute) -> COPY (copy_expert) -> TRUNCATE (execute) -> INSERT (execute)
    assert call_order == ["execute", "copy_expert", "execute", "execute"], (
        "load must COPY into staging before truncating raw.<table>, and truncate "
        "before inserting — this is what makes a malformed CSV fail safely "
        "without wiping existing good data"
    )
    fake_conn.commit.assert_called_once()
    fake_conn.rollback.assert_not_called()
    fake_conn.close.assert_called_once()


def test_load_to_postgres_rolls_back_and_reraises_on_failure():
    from itsm_raw_ingestion import _load_to_postgres

    fake_cursor, fake_conn = _fake_cursor_and_conn()
    fake_cursor.copy_expert.side_effect = RuntimeError("malformed CSV")

    with patch("itsm_raw_ingestion.S3Hook") as mock_s3hook, \
         patch("itsm_raw_ingestion.PostgresHook") as mock_pghook, \
         patch("psycopg2.sql.Composed.as_string", return_value="COPY staging (...) FROM STDIN ..."):
        mock_s3hook.return_value.read_key.return_value = "bad data"
        mock_pghook.return_value.get_conn.return_value = fake_conn

        with pytest.raises(RuntimeError):
            _load_to_postgres(STAFF, ds="2026-01-15")

    fake_conn.commit.assert_not_called()
    fake_conn.rollback.assert_called_once()
    fake_conn.close.assert_called_once()


def test_extract_to_s3_uploads_with_deterministic_key_and_replace_true():
    from itsm_raw_ingestion import _extract_to_s3

    with patch("itsm_raw_ingestion.S3Hook") as mock_s3hook:
        mock_hook = mock_s3hook.return_value
        _extract_to_s3(STAFF, ds="2026-01-15")

    mock_hook.load_file.assert_called_once()
    _, kwargs = mock_hook.load_file.call_args
    assert kwargs["bucket_name"] == "itsm-raw-zone"
    assert kwargs["key"] == "staff/dt=2026-01-15/staff_20260115.csv"
    assert kwargs["replace"] is True
