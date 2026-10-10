"""
Phase 1 ingestion DAG: extract synthetic ITSM source data, land in the S3 raw
zone, load into the Postgres `raw` landing schema.

Task 9 of the DAG build (see LEARNING_LOG.md) — truncate-and-load per table,
so re-running (manual or scheduled) leaves row counts unchanged instead of
duplicating. One TaskGroup per source table, matching the per-table TaskGroup
shape decided in the Step 2 architecture plan.
"""
import io
import logging

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.task_group import TaskGroup
from psycopg2 import sql

from itsm_common.config import DATA_DIR, S3_BUCKET
from itsm_common.s3_keys import s3_key_for
from itsm_common.tables import TABLES, TableConfig

log = logging.getLogger(__name__)


def _extract_to_s3(table: TableConfig, **context) -> None:
    local_path = DATA_DIR / f"{table.name}.csv"
    key = s3_key_for(table.name, context["ds"])
    S3Hook(aws_conn_id="aws_s3").load_file(
        filename=str(local_path),
        key=key,
        bucket_name=S3_BUCKET,
        replace=True,  # re-triggering the same logical date overwrites, doesn't duplicate
    )
    log.info("uploaded %s -> s3://%s/%s", local_path, S3_BUCKET, key)


def _load_to_postgres(table: TableConfig, **context) -> None:
    key = s3_key_for(table.name, context["ds"])
    csv_text = S3Hook(aws_conn_id="aws_s3").read_key(key, bucket_name=S3_BUCKET)

    # Identifiers built with psycopg2.sql rather than f-string interpolation —
    # table/column names come from our own trusted TABLES config, not user
    # input, so there's no real injection risk here, but this is the correct
    # habit regardless of whether a given instance is exploitable.
    raw_table = sql.Identifier("raw", table.name)
    columns = sql.SQL(", ").join(sql.Identifier(c) for c in table.columns)

    conn = PostgresHook(postgres_conn_id="postgres_warehouse").get_conn()
    try:
        with conn.cursor() as cur:
            # LIKE ... INCLUDING DEFAULTS pulls the staging table's shape (and
            # types) straight from raw.<table> — no column/type list duplicated
            # here that could drift from sql/landing_schema.sql.
            cur.execute(sql.SQL("CREATE TEMP TABLE staging (LIKE {} INCLUDING DEFAULTS)").format(raw_table))
            cur.copy_expert(
                sql.SQL("COPY staging ({}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')")
                .format(columns).as_string(conn),
                io.StringIO(csv_text),
            )
            # Truncate only after COPY has already succeeded into staging — a
            # malformed CSV fails at COPY, before this line, leaving existing
            # good data in raw.<table> untouched rather than wiped for nothing.
            cur.execute(sql.SQL("TRUNCATE {}").format(raw_table))
            # _source_key traces this row back to the exact S3 object it came
            # from; _ingested_at is left off so raw.<table>'s own DEFAULT
            # now() applies at insert time.
            cur.execute(
                sql.SQL("INSERT INTO {} ({}, _source_key) SELECT {}, %s FROM staging")
                .format(raw_table, columns, columns),
                (key,),
            )
        conn.commit()
    except Exception:
        # Explicit, not relied-upon-implicitly: closing an uncommitted
        # connection happens to abort the transaction today, but that's a
        # psycopg2 implementation detail, not a stated contract — stating it
        # here means the guarantee survives a future switch to pooled
        # connections (SQLAlchemy engine, PgBouncer session pooling, etc.).
        conn.rollback()
        raise
    finally:
        conn.close()

    log.info("loaded s3://%s/%s -> raw.%s", S3_BUCKET, key, table.name)


with DAG(
    dag_id="itsm_raw_ingestion",
    description="Extract synthetic ITSM source data, land in S3 raw zone, load into Postgres landing schema",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["phase-1", "phase-2", "raw-ingestion", "dbt"],
) as dag:
    table_groups = []
    for table in TABLES:
        with TaskGroup(group_id=table.name) as tg:
            extract = PythonOperator(
                task_id="extract_to_s3",
                python_callable=_extract_to_s3,
                op_kwargs={"table": table},
            )
            load = PythonOperator(
                task_id="load_to_postgres",
                python_callable=_load_to_postgres,
                op_kwargs={"table": table},
            )
            extract >> load
        table_groups.append(tg)

    # One project-wide task, not per table: dbt build needs all 8 raw tables
    # landed, and parallel runs would collide on the same target schemas.
    # DBT_PROFILES_DIR / DBT_DB_PASSWORD come from the container env.
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command="/opt/airflow/dbt_venv/bin/dbt build --project-dir /opt/airflow/dbt/itsm_analytics",
        retries=0,
    )

    table_groups >> dbt_build
