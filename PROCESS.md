# Process — itsm-data-platform

This repository is a 4-project data engineering portfolio, built to
demonstrate modern data engineering tooling.

## The throughline
All four projects operate on the same simulated data domain — an IT-services company's operational data (helpdesk/ticketing, managed services, professional services) — solved four different ways as the architecture evolves. This is intentional: rather than four unrelated demos, the portfolio demonstrates depth in one problem space across four architectural paradigms, the way a real data platform actually evolves inside a company.

| # | Project | Paradigm |
|---|---------|----------|
| 1 | `projects/etl-pipeline` | Batch ELT — dbt, Airflow, Docker, LocalStack, Postgres |
| 2 | `projects/streaming-pipeline` | Streaming/CDC — Kafka/Redpanda, Spark Structured Streaming or Flink |
| 3 | `projects/data-quality-framework` | Data quality & observability — Great Expectations/dbt tests, Airflow alerting |
| 4 | `projects/lakehouse` | Lakehouse — MinIO, Iceberg or Delta Lake, Trino/DuckDB |

Everything runs locally via Docker — no paid services, subscriptions, or licenses.

## Data
Data across all four projects is synthetic or adapted from public datasets resembling IT-services company operations. No real company or client data, and no real PII, appears anywhere in this repository. See each project's own `PROCESS.md` for the specific dataset(s) it uses.

## Per-project detail
Each project folder has its own `PROCESS.md` covering that project's build phases, specific design decisions, and an "if this were production" section on what would change with real cloud infrastructure and budget.
