-- Grain: one row per incident. Star-schema fact — FKs and measures only,
-- same reasoning as fact_helpdesk_ticket (int_incidents_enriched stays around
-- as the flattened, name-joined alternative).
select
    incident_id,
    cast(opened_at as date) as opened_date,
    cast(closed_at as date) as closed_date,
    opened_at,
    closed_at,
    asset_id,
    client_id,
    assigned_technician_id,
    severity,
    incident_source,
    incident_status,
    is_resolved,
    resolution_hours
from {{ ref('int_incidents_enriched') }}
