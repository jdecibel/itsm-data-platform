-- Read-only role for any tool or process that should never be able to write
-- (automated tests, reporting/BI, ad-hoc inspection). SELECT-only on the raw
-- schema now, and automatically on any future schema's tables via default
-- privileges — no need to remember to re-grant when Phase 2 adds staging/marts.
--
-- Invoked with: psql ... -v ON_ERROR_STOP=1 -v ro_password="$WAREHOUSE_RO_PASSWORD" -f readonly_role.sql
--
-- No DO $$ ... $$ block here on purpose: psql's :'var' substitution does not
-- reach inside dollar-quoted bodies, so CREATE ROLE ... PASSWORD :'ro_password'
-- inside DO $$ ... $$ sends the literal, unsubstituted text to Postgres and
-- fails with a syntax error. \gexec sidesteps this — build the DDL as a
-- string (substitution applies normally here, outside any $$ quoting), then
-- execute whatever string each row returns.

SELECT 'CREATE ROLE warehouse_readonly LOGIN PASSWORD ' || quote_literal(:'ro_password')
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'warehouse_readonly')
\gexec

SELECT 'ALTER ROLE warehouse_readonly PASSWORD ' || quote_literal(:'ro_password')
WHERE EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'warehouse_readonly')
\gexec

GRANT CONNECT ON DATABASE itsm_warehouse TO warehouse_readonly;
GRANT USAGE ON SCHEMA raw TO warehouse_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO warehouse_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO warehouse_readonly;
