-- Dedicated role for dbt: SELECT on raw (it only reads from there), CREATE on
-- the three analytics schemas (it materializes staging/intermediate/mart
-- models there). Kept separate from `warehouse` (the ingestion DAG's role)
-- and `warehouse_readonly` (SELECT-only reporting/tooling role) — same
-- "enforce access at the DB level, not by convention" precedent as Phase 1's
-- read-only role.
--
-- Invoked with: psql ... -v ON_ERROR_STOP=1 -v dbt_password="$DBT_DB_PASSWORD" -f dbt_role.sql
--
-- Uses \gexec instead of a DO $$ ... $$ block for the same reason
-- readonly_role.sql does — psql's :'var' substitution doesn't reach inside
-- dollar-quoted bodies.

SELECT 'CREATE ROLE dbt LOGIN PASSWORD ' || quote_literal(:'dbt_password')
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dbt')
\gexec

SELECT 'ALTER ROLE dbt PASSWORD ' || quote_literal(:'dbt_password')
WHERE EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dbt')
\gexec

GRANT CONNECT ON DATABASE itsm_warehouse TO dbt;

-- dbt reads raw as its only source.
GRANT USAGE ON SCHEMA raw TO dbt;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO dbt;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO dbt;

-- Pre-create the three schemas dbt materializes into. dbt's own
-- CREATE SCHEMA IF NOT EXISTS at runtime is then a no-op — pre-creating them
-- here is what lets us set default privileges below, since ALTER DEFAULT
-- PRIVILEGES IN SCHEMA needs the schema to already exist.
CREATE SCHEMA IF NOT EXISTS staging AUTHORIZATION dbt;
CREATE SCHEMA IF NOT EXISTS intermediate AUTHORIZATION dbt;
CREATE SCHEMA IF NOT EXISTS marts AUTHORIZATION dbt;

-- warehouse_readonly can browse the analytics layer too, same as raw —
-- "FOR ROLE dbt" matters here: these schemas' future objects are created BY
-- the dbt role, not by whichever role happens to run this bootstrap script.
GRANT USAGE ON SCHEMA staging, intermediate, marts TO warehouse_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE dbt IN SCHEMA staging GRANT SELECT ON TABLES TO warehouse_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE dbt IN SCHEMA intermediate GRANT SELECT ON TABLES TO warehouse_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE dbt IN SCHEMA marts GRANT SELECT ON TABLES TO warehouse_readonly;
