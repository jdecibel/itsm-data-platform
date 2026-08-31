# itsm-data-platform

A 4-project data engineering portfolio built around one simulated data domain — an IT-services company's operational data (helpdesk/ticketing, managed services, professional services) — solved four different ways as the architecture evolves. See [`PROCESS.md`](PROCESS.md) for the full narrative behind why it's structured this way.

| # | Project | Paradigm | Status |
|---|---------|----------|--------|
| 1 | [`projects/etl-pipeline`](projects/etl-pipeline) | Batch ELT — dbt, Airflow, Docker, LocalStack, Postgres | Phase 1 complete |
| 2 | `projects/streaming-pipeline` | Streaming/CDC — Kafka/Redpanda, Spark Structured Streaming or Flink | Not started |
| 3 | `projects/data-quality-framework` | Data quality & observability — Great Expectations/dbt tests, Airflow alerting | Not started |
| 4 | `projects/lakehouse` | Lakehouse — MinIO, Iceberg or Delta Lake, Trino/DuckDB | Not started |

Everything runs locally via Docker — no paid services, subscriptions, or licenses. Each project is self-contained (its own `docker-compose.yml`, dependencies, README) — see each project's own README for how to run it.

No real company or client data, and no real PII, anywhere in this repository — all data is synthetic or adapted from public datasets.
