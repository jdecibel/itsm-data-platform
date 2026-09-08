-- Singular test: fails if any incident's closed_at is before its opened_at.
-- dbt singular tests pass when the query returns zero rows.
select *
from {{ ref('int_incidents_enriched') }}
where closed_at < opened_at
