# Process

This project is Project 1 of a 4-part data engineering portfolio, built to demonstrate modern data engineering tooling (Airflow, dbt, Docker, cloud-pattern local tooling).

## Portfolio approach
All four projects use the same data domain — IT-services company data (helpdesk/ticketing, managed services, professional services) — so the portfolio demonstrates depth in one problem space across four different architectural paradigms, rather than four unrelated demos:

1. **Batch ELT pipeline** (this project) — dbt, Airflow, Docker, LocalStack, Postgres
2. **Streaming/CDC pipeline** — Kafka/Redpanda, Spark Structured Streaming or Flink
3. **Data quality & observability framework** — Great Expectations/dbt tests, Airflow alerting
4. **Data lakehouse** — MinIO, Iceberg or Delta Lake, Trino/DuckDB

Everything runs locally via Docker — no paid services, subscriptions, or licenses were used.

## This project's build phases
1. **Infrastructure + raw ingestion** — Docker-based Airflow, Postgres, and LocalStack (S3-compatible storage); raw IT-services data landed in an S3 raw zone, then loaded into a Postgres landing schema.
2. **Transformation layer** — dbt staging, intermediate, and mart models forming a dimensional model over the raw data, with schema tests.
3. **Incremental loads + orchestration hardening** — incremental loading, idempotent re-runs, backfill support, and failure handling for realistic data edge cases.
4. **Analytics layer + polish** — a lightweight BI layer over the mart tables, final architecture documentation, and a review of what would change with real production infrastructure and budget.

## Data
Data is synthetic/adapted from a public dataset resembling IT-services company operations — no real company or client data is used anywhere in this project.

## Note on first run
Airflow pauses newly-discovered DAGs by default — a deliberate Airflow safety default (don't auto-run a DAG nobody's reviewed yet), kept as-is here rather than overridden. After `docker compose up`, `itsm_raw_ingestion` needs to be unpaused once before it will actually run: either toggle it in the UI (`http://localhost:8081`) or run `docker compose exec airflow-scheduler airflow dags unpause itsm_raw_ingestion`.

## Notes on scope
This is a portfolio project built for learning and demonstration purposes, not a production system. Design decisions favor clarity and realistic patterns over production-grade scale or cost optimization; where relevant, this README calls out what would change for an actual production deployment.
