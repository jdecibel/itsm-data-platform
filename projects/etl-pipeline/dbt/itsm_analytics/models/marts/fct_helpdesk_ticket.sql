-- Grain: one row per helpdesk ticket. Star-schema fact — carries FKs and
-- measures only, not the descriptive names int_helpdesk_tickets_enriched
-- joins in for readability (that model stays available as a flattened,
-- ad-hoc-query-friendly alternative; this one is what BI tools/other facts
-- join against).
select
    ticket_id,
    cast(created_at as date) as created_date,
    cast(resolved_at as date) as resolved_date,
    created_at,
    resolved_at,
    requested_by_employee_id,
    assigned_technician_id,
    category,
    priority,
    ticket_status,
    is_resolved,
    resolution_hours
from {{ ref('int_helpdesk_tickets_enriched') }}
