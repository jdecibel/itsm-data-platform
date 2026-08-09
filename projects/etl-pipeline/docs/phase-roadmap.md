# Project 1 (etl-pipeline) — Full Phase Roadmap

Location in monorepo: `projects/etl-pipeline/`

Each phase should be its own Claude Code session (or a small number of sessions), scoped tightly, committed to git at completion before moving on.

## Phase 1 — Infra + Raw Ingestion (current)
**Goal:** Prove the skeleton works end-to-end with zero transformation logic.
- Docker Compose: Airflow (webserver/scheduler/init), Postgres, LocalStack
- LocalStack S3 bucket structure for the raw zone (naming/partitioning)
- Postgres landing schema (raw, untransformed structure)
- Airflow DAG: extract from source → land in S3 raw zone → load raw into Postgres landing schema
- **CI:** none yet — infra still stabilizing
- **Explicitly excluded:** dbt, any transformation/business logic, data modeling beyond raw landing structure
- **Definition of done:** DAG runs end-to-end on a schedule/manual trigger, raw IT-services data (helpdesk, managed services, professional services) is queryable in the Postgres landing schema, README documents the architecture and the S3-first design decision

## Phase 2 — Transformation Layer (dbt)
**Goal:** Turn raw landing data into a proper dimensional model.
- Introduce dbt, connected to the Postgres landing schema as source
- Staging models (1:1 cleanup of raw sources — type casting, renaming, basic null handling)
- Intermediate models (business logic joins/aggregations across the three IT-services sub-domains)
- Mart models — a dimensional model: likely fact tables for tickets, incidents, and timesheets/billing, with shared dimensions (client, technician/agent, asset, project, date)
- dbt tests: schema tests (not_null, unique, relationships) at minimum
- **CI:** add a minimal GitHub Actions workflow that runs `dbt test` on push
- **Explicitly excluded:** incremental models, orchestration hardening, alerting — dbt runs as a single full-refresh Airflow task for now
- **Definition of done:** `dbt run` + `dbt test` succeed end-to-end via Airflow AND in CI, mart tables reflect a coherent dimensional model, dbt docs generated, README explains the modeling decisions (why this grain, why these dimensions)

## Phase 3 — Incremental Loads + Orchestration Hardening
**Goal:** Make the pipeline behave like something that could actually run in production, not just once.
- Convert full-refresh ingestion/dbt runs to incremental where it makes sense (e.g. incremental ticket/timesheet loads by updated_at or load date)
- Idempotency: pipeline must be safely re-runnable on the same day/batch without creating duplicates
- Backfill support: document/demonstrate how to reprocess a historical date range
- Basic failure handling: retries, task-level alerting (even just an Airflow email/webhook on failure is enough — no paid service)
- Handle realistic edge cases in the data: duplicate records, late-arriving records, malformed rows — decide and document how each is handled
- **CI:** extend the GitHub Actions workflow to spin up the full Dockerstack and run the DAG end-to-end as an integration test (not just `dbt test` in isolation)
- **Definition of done:** can demonstrate an idempotent re-run, a backfill of a past date range, and at least one deliberately-injected edge case (e.g. a malformed row) being handled gracefully rather than crashing the DAG — AND the CI integration test passes on a clean checkout

## Phase 4 — Analytics Layer + Portfolio Polish
**Goal:** Make the output consumable and the project presentable as a finished portfolio piece.
- Expose the mart layer via a lightweight local BI tool (Metabase or Superset, self-hosted, free) — a couple of representative dashboards/queries (e.g. ticket volume trends, SLA breach rate, billable vs. non-billable hours)
- Final architecture diagram (can stay text/ASCII) covering the full pipeline end-to-end across all 4 phases
- **CI:** add a status badge to the project README reflecting the Phase 2/3 CI workflows
- Final README pass: problem statement, architecture, design tradeoffs made at each phase, "if this were production" section (what would change with real cloud infra/budget — e.g. Redshift/Snowflake instead of Postgres, real S3 instead of LocalStack, Airflow on managed infra/MWAA)
- Clean commit history check — squash any messy WIP commits if needed

## Notes for later phases (subject to refinement)
- Exact dbt mart grain and dimension list should be finalized once the actual dataset is chosen in Phase 1 — don't lock these in prematurely.
- If Phase 1's dataset choice turns out to be a poor fit for incremental logic in Phase 3, that's worth flagging early rather than discovering it mid-Phase-3.
