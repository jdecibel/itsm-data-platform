select
    i.incident_id,
    i.asset_id,
    a.asset_type,
    i.client_id,
    c.client_name,
    i.opened_at,
    i.closed_at,
    i.severity,
    i.incident_source,
    i.assigned_technician_id,
    tech.staff_name as technician_name,
    i.incident_status,
    (i.closed_at is not null) as is_resolved,
    -- null (not zero) while still open — same reasoning as the ticket model.
    extract(epoch from (i.closed_at - i.opened_at)) / 3600.0 as resolution_hours
from {{ ref('stg_incidents') }} i
left join {{ ref('stg_assets') }} a on i.asset_id = a.asset_id
left join {{ ref('stg_clients') }} c on i.client_id = c.client_id
left join {{ ref('stg_staff') }} tech on i.assigned_technician_id = tech.staff_id
