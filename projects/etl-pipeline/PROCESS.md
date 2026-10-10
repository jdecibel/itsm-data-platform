# Process

This project is Project 1 of a 4-part data engineering portfolio — see [`../../PROCESS.md`](../../PROCESS.md) for the portfolio-wide rationale and [`README.md`](README.md) for this project's architecture and how to run it.

## This project's build phases
1. **Infrastructure + raw ingestion** — Docker-based Airflow, Postgres, and LocalStack (S3-compatible storage); raw IT-services data landed in an S3 raw zone, then loaded into a Postgres landing schema. ✅ Complete.
2. **Transformation layer** — dbt staging, intermediate, and mart models forming a dimensional model over the raw data, with schema tests. ✅ Complete (21 models, 103 data tests, wired into the DAG, CI via GitHub Actions).
3. **Incremental loads + orchestration hardening** — incremental loading, idempotent re-runs, backfill support, and failure handling for realistic data edge cases.
4. **Analytics layer + polish** — a lightweight BI layer over the mart tables, final architecture documentation, and a review of what would change with real production infrastructure and budget.

## Data
Data is synthetic/adapted from a public dataset resembling IT-services company operations — no real company or client data is used anywhere in this project. See `README.md` for the specific dataset and how to obtain it.

## Notes on scope
This is a portfolio project built for learning and demonstration purposes, not a production system. Design decisions favor clarity and realistic patterns over production-grade scale or cost optimization — see `README.md`'s "if this were production" section for what would change with real infrastructure and budget.
