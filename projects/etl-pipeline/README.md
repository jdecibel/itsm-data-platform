# etl-pipeline

Project 1 of a 4-part data engineering portfolio: a batch ELT pipeline for a simulated IT-services company's operational data (helpdesk/ticketing, managed services, professional services). Phase 1 — infra + raw ingestion — is complete: raw source data lands in an S3 raw zone, then loads into a typed Postgres landing schema, orchestrated by Airflow, running entirely in Docker at $0.

See [`../../PROCESS.md`](../PROCESS.md) for how this project fits the wider 4-project portfolio, and [`docs/phase-roadmap.md`](docs/phase-roadmap.md) for the full phase breakdown.

## Architecture

```
 data/source/it_service_tickets.csv (real, Kaggle)
              │
              ▼
   scripts/generate_synthetic_data.py
              │
              ▼
   data/synthetic/*.csv  (8 source tables)
              │
              │  Airflow DAG: itsm_raw_ingestion (one TaskGroup per table)
              │
   ┌──────────┴───────────┐
   │   extract_to_s3       │   reads the local CSV, uploads as-is
   └──────────┬───────────┘
              ▼
   LocalStack S3 — s3://itsm-raw-zone/<table>/dt=<date>/<table>_<date>.csv
              │
   ┌──────────┴───────────┐
   │   load_to_postgres    │   downloads from S3, COPYs into staging,
   └──────────┬───────────┘   truncates raw.<table>, INSERT...SELECT
              ▼
   Postgres (postgres-warehouse) — raw.<table>, typed, no constraints yet
```

Two separate Postgres instances: `postgres-airflow` holds Airflow's own operational metadata (DAG runs, task history), `postgres-warehouse` holds the actual pipeline data. Kept apart so iterating on the landing schema never risks Airflow's own bookkeeping, and so `postgres-airflow` never needs a host port exposed at all.

## Why land in S3 before Postgres (and not skip straight to the warehouse)

The load task downloads its input from S3 — it does not read the local CSV directly, even though the same process that runs `extract_to_s3` already has that file on disk. Two reasons this isn't redundant:

- **Extract and load are independent failure domains.** If the warehouse is down, the extract still succeeds and the raw file is durably sitting in S3, ready to load whenever the warehouse comes back — nothing needs to be re-extracted from the source.
- **It's the standard cloud ELT shape.** A raw/bronze zone in object storage, landed before anything touches a warehouse, is how this looks in a real AWS/GCP/Azure pipeline — LocalStack stands in for S3 here for the same reason Postgres stands in for a cloud warehouse: same pattern, $0 cost, fully local.

## Design decisions worth knowing

- **Typed landing schema, but deliberately no `PRIMARY KEY`/`NOT NULL`/foreign key constraints** (`sql/landing_schema.sql`). Uniqueness/not-null/relationship checks are Phase 2's job, via dbt schema tests — enforcing them at landing time would mean one malformed source row fails an entire day's load, which defeats the point of a raw landing zone (land it as-is, judge its quality separately).
- **Truncate-and-load, not incremental.** Matches Phase 1's full-refresh scope; incremental loads and backfill are Phase 3. `_load_to_postgres` truncates `raw.<table>` only *after* `COPY` has already succeeded into a staging table — a malformed CSV fails before the truncate is ever reached, so bad input never wipes good existing data.
- **One bucket (`itsm-raw-zone`), not one per table**, with per-table key prefixes (`<table>/dt=<date>/...`) instead. An IAM policy scoped to the bucket covers every table's prefix automatically; per-table buckets would mean an IAM change every time a table is added.
- **A read-only Postgres role** (`warehouse_readonly`, `sql/readonly_role.sql`) exists for any tool that should only ever read — enforced at the database level (`GRANT SELECT` only), not just by convention.
- **New DAGs start paused** (Airflow's own default, kept intentionally) — unpause `itsm_raw_ingestion` once after a fresh `docker compose up`, either in the UI or via `airflow dags unpause itsm_raw_ingestion`.

## Running it locally

1. Get the real anchor dataset — ["IT Service Ticket Classification"](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification) (Kaggle, adisongoh) — and place it at `data/source/it_service_tickets.csv`. `data/` is gitignored; nobody's data ships in this repo.
2. `pip install -r scripts/requirements.txt && python scripts/generate_synthetic_data.py` — generates the 8 synthetic source CSVs into `data/synthetic/`.
3. `cp .env.example .env`
4. `docker compose up -d` — brings up Airflow (webserver on `:8081`), the two Postgres instances, and LocalStack; bootstraps the S3 bucket and the landing schema automatically.
5. Unpause the DAG once: `docker compose exec airflow-scheduler airflow dags unpause itsm_raw_ingestion`, then trigger it from the UI or `airflow dags trigger itsm_raw_ingestion`.

## Verifying it worked

```bash
# row counts should match each source CSV's line count minus its header
docker compose exec postgres-warehouse psql -U warehouse -d itsm_warehouse \
  -c "SELECT 'staff', count(*) FROM raw.staff UNION ALL SELECT 'helpdesk_tickets', count(*) FROM raw.helpdesk_tickets;"

# objects should exist under the agreed key convention
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 \
  aws --endpoint-url=http://localhost:4566 s3 ls --recursive s3://itsm-raw-zone/
```

Automated tests live in `tests/` — pure logic (`s3_key_for`, the table config) runs anywhere with `pytest`; the mocked task-logic tests need Airflow installed, so run them inside the container: `docker compose exec airflow-scheduler sh -c "pip install -q pytest && PYTHONPATH=/opt/airflow/dags python -m pytest /opt/airflow/tests"`.

## If this were production

This runs at $0 on a laptop, which shapes several decisions that would change with a real cloud budget and real production data volume:

- **No S3 lifecycle policy.** Every `@daily` run currently re-uploads a full snapshot of all 8 tables under a new `dt=` partition, forever — there's no expiry rule on old partitions. At real volume this is a real, compounding storage cost; a production raw zone needs a lifecycle rule to expire partitions past a retention window.
- **The extract is a full re-dump, not a true incremental extract**, because the "source system" here is a static file, not a live database with an `updated_at` column to extract deltas from. A real source system would support (and this pipeline would need) genuine incremental extraction.
- **Loading the whole file into memory as a Python string won't scale.** `_load_to_postgres` pulls the entire S3 object into memory before copying it into Postgres. Fine at a few thousand rows; a multi-GB real extract needs to stream bytes directly from S3 into the load instead, or use the warehouse's own native bulk-load-from-object-storage feature (e.g. Redshift `COPY FROM 's3://...'`, Snowflake `COPY INTO`).
- **`TRUNCATE`-then-`INSERT` has a brief visibility gap** — between the truncate and the insert completing, any concurrent reader sees an empty table, not stale-but-consistent data. Invisible at this speed and volume; a real production load would build into a new table and atomically rename it in, so the table is always either fully old or fully new to any reader.
- **Connection secrets are plaintext env vars** (`AIRFLOW_CONN_*` in `docker-compose.yml`) — correct and standard for local dev, but a real deployment would back Airflow connections with a secrets manager (AWS Secrets Manager, Vault) instead.
- **No connection pooling.** A fresh Postgres connection per table per run is nothing at 8 tables; a much larger table count or a much tighter schedule would need PgBouncer or pooled hooks to avoid connection churn.
- **Managed infra instead of local Docker** — Airflow on MWAA/Composer, real S3, Redshift/Snowflake/BigQuery instead of Postgres.
