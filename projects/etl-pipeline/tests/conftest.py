"""
Puts dags/ on sys.path so `itsm_common` and `itsm_raw_ingestion` are
importable from tests, without needing the Airflow-specific PYTHONPATH
workaround at invocation time.

Works the same whether tests/ sits next to dags/ on the host
(projects/etl-pipeline/{tests,dags}) or inside the Airflow container
(/opt/airflow/{tests,dags}) — both mirror the same relative layout.
"""
import sys
from pathlib import Path

DAGS_DIR = Path(__file__).resolve().parents[1] / "dags"
if str(DAGS_DIR) not in sys.path:
    sys.path.insert(0, str(DAGS_DIR))
