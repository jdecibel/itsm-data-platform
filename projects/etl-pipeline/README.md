# etl-pipeline

Project 1 of a 4-part data engineering portfolio: a batch ELT pipeline for a simulated IT-services company's operational data (helpdesk/ticketing, managed services, professional services). Raw source data lands in an S3 raw zone, loads into a typed Postgres landing schema, and is then transformed by dbt into a star schema (staging → intermediate → marts) with 103 data tests — all orchestrated by one Airflow DAG, built with CI, and running entirely in Docker at $0. Phases 1 (infra + raw ingestion) and 2 (dbt transformation + CI) are complete.

Built with Claude Code as a pair programmer; design decisions and trade-offs are documented below.

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
              │
              │  after all 8 table groups finish: one `dbt build` task
              ▼
   dbt (itsm_analytics):  raw ─► staging ─► intermediate ─► marts
                                  8 views     4 views       5 dim_ + 4 fact_ tables
```

Two separate Postgres instances: `postgres-airflow` holds Airflow's own operational metadata (DAG runs, task history), `postgres-warehouse` holds the actual pipeline data. Kept apart so iterating on the landing schema never risks Airflow's own bookkeeping, and so `postgres-airflow` never needs a host port exposed at all.

## Why land in S3 before Postgres (and not skip straight to the warehouse)

The load task downloads its input from S3 — it does not read the local CSV directly, even though the same process that runs `extract_to_s3` already has that file on disk. Two reasons this isn't redundant:

- **Extract and load are independent failure domains.** If the warehouse is down, the extract still succeeds and the raw file is durably sitting in S3, ready to load whenever the warehouse comes back — nothing needs to be re-extracted from the source.
- **It's the standard cloud ELT shape.** A raw/bronze zone in object storage, landed before anything touches a warehouse, is how this looks in a real AWS/GCP/Azure pipeline — LocalStack stands in for S3 here for the same reason Postgres stands in for a cloud warehouse: same pattern, $0 cost, fully local.

## Transformation layer (dbt)

The dbt project lives in `dbt/itsm_analytics/`. Each layer has its own folder, schema and materialization, and layers only depend forward (`raw → staging → intermediate → marts`):

| Layer | Schema | Built as | What it does |
|---|---|---|---|
| `staging/` | `staging` | views | 1:1 cleanup of each raw table (entity-prefixed renames like `ticket_status`, lineage columns dropped). Owns value-range tests (`accepted_values`, `hours > 0`). |
| `intermediate/` | `intermediate` | views | Joins and business logic computed once: `resolution_hours` (null, not zero, while unresolved), `is_resolved`, and a project-grain reconciliation of timesheet hours vs invoiced amount. Reads staging only. |
| `marts/` | `marts` | tables | The star schema: `dim_date`, `dim_client`, `dim_staff` (role-playing — one dimension joined as requester, technician, project manager and employee), `dim_asset`, `dim_project`, and `fact_helpdesk_ticket`, `fact_incident`, `fact_timesheet_entry`, `fact_invoice`. Owns the fact-to-dimension `relationships` tests. |

Every model has its own `<model>.yml` with descriptions and tests next to its `.sql`. Run `dbt docs generate` for the lineage graph and column docs.

Decisions worth knowing:

- **dbt runs as one task, after all 8 ingestion groups** — `dbt build` reads every raw table, and per-table dbt runs would hit missing sources and collide writing to the same schemas. `dbt build` also runs the tests, so a failing data test fails the DAG: the pipeline is its own data-quality gate.
- **dbt lives in its own virtualenv inside a custom Airflow image** (`Dockerfile`), because dbt-core's pinned dependencies conflict with Airflow's own.
- **A dedicated `dbt` Postgres role** (`sql/dbt_role.sql`) with `SELECT` on `raw` and rights only on the three transformation schemas; `warehouse_readonly` gets read access to everything dbt builds via default privileges.
- **Natural keys, no surrogate keys** — the source IDs (`CLI-0001`, `EMP-00001`) are clean and stable. Revisit if slowly changing dimensions are added.
- **Timesheets and invoices are two separate facts** — the source has no row-level link between them (invoices attach to projects, not timesheet lines), so they're reconciled only at project grain rather than faking a relationship.
- **`not_null` on a helpdesk ticket's assigned technician is scoped to non-Open tickets** — about 40% of Open tickets are legitimately unassigned, so the test still catches a real bug (a non-Open ticket with nobody assigned) without failing on expected data.
- **SLA breach tracking is deliberately not modeled** — the source has no SLA targets to measure against.

## CI

`.github/workflows/dbt.yml` runs on pushes and PRs that touch the dbt project: it starts a throwaway Postgres service container, loads the committed fixtures in `ci/fixtures/` into `raw.*` using the real `sql/landing_schema.sql` (via `ci/load_fixtures.sh`), then runs `dbt build --target ci` — every model and all 103 tests. The fixtures are small but include the edge cases the tests care about (unresolved tickets, open incidents, unassigned Open tickets, a project with no timesheets or invoices).

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
5. Unpause the DAG once: `docker compose exec airflow-scheduler airflow dags unpause itsm_raw_ingestion`, then trigger it from the UI or `airflow dags trigger itsm_raw_ingestion`. The run ends with the `dbt_build` task, which builds the star schema and runs all data tests.
6. Optional: browse the dbt docs — `docker compose exec airflow-scheduler /opt/airflow/dbt_venv/bin/dbt docs generate --project-dir /opt/airflow/dbt/itsm_analytics`, then `cd dbt/itsm_analytics/target && python3 -m http.server 8082` and open `http://localhost:8082`.

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
- **dbt models are full-refresh.** Marts rebuild from scratch every run. Real volume would need incremental models on the large facts, and slowly changing dimension history (SCD type 2) for things like staff role changes — which would also be the point to revisit natural vs surrogate keys.
- **dbt runs inside the Airflow container via `BashOperator`.** Fine here; at scale you'd run dbt as its own isolated task (a container operator or a dedicated runner), and break the single `dbt build` into per-model or per-selector tasks for finer retries and visibility.
- **No source freshness checks or alerting.** A production pipeline would add `dbt source freshness`, failure notifications, and data-quality monitoring beyond pass/fail tests.
- **Managed infra instead of local Docker** — Airflow on MWAA/Composer, real S3, Redshift/Snowflake/BigQuery instead of Postgres.
