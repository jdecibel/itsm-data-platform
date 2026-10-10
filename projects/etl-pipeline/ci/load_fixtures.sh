#!/usr/bin/env bash
# Loads the committed CI fixtures into a Postgres database as raw.* — the same
# landing tables Phase 1 creates (sql/landing_schema.sql), so dbt in CI reads
# exactly the shape it reads locally. Connection comes from the standard libpq
# env vars: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

psql -v ON_ERROR_STOP=1 -f "$DIR/../sql/landing_schema.sql"

for csv in "$DIR"/fixtures/*.csv; do
  table="$(basename "$csv" .csv)"
  # Column list is read from each CSV's own header, so lineage columns
  # (_ingested_at, _source_key) fall back to their table defaults.
  columns="$(head -1 "$csv")"
  psql -v ON_ERROR_STOP=1 -c "\copy raw.${table} (${columns}) FROM '${csv}' WITH (FORMAT csv, HEADER true, NULL '')"
done
