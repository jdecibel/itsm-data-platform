select
    incident_id,
    asset_id,
    client_id,
    opened_at,
    closed_at,
    severity,
    source as incident_source,
    assigned_technician_id,
    status as incident_status,
    _ingested_at as loaded_at
from {{ source('raw', 'incidents') }}
