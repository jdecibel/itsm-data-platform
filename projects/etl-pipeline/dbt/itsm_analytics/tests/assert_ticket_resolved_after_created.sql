-- Singular test: fails if any ticket's resolved_at is before its created_at.
-- Mirrors assert_incident_closed_after_opened.sql — tickets have the same
-- nullable-resolution shape as incidents but never got the equivalent check.
select *
from {{ ref('int_helpdesk_tickets_enriched') }}
where resolved_at < created_at
