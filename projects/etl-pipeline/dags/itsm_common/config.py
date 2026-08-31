"""Shared infra constants for the ingestion DAG."""
from pathlib import Path

S3_BUCKET = "itsm-raw-zone"
DATA_DIR = Path("/opt/airflow/data/synthetic")
