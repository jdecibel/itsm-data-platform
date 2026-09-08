select
    ticket_id,
    created_at,
    resolved_at,
    category,
    description,
    requested_by_employee_id,
    assigned_technician_id,
    priority,
    status as ticket_status,
    _ingested_at as loaded_at
from {{ source('raw', 'helpdesk_tickets') }}
