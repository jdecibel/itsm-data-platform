select
    t.ticket_id,
    t.created_at,
    t.resolved_at,
    t.category,
    t.description,
    t.priority,
    t.ticket_status,
    t.requested_by_employee_id,
    requester.staff_name as requester_name,
    t.assigned_technician_id,
    assignee.staff_name as assignee_name,
    (t.resolved_at is not null) as is_resolved,
    -- null (not zero) for unresolved tickets — resolved_at is null, so the
    -- subtraction propagates null rather than producing a fake duration.
    extract(epoch from (t.resolved_at - t.created_at)) / 3600.0 as resolution_hours
from {{ ref('stg_helpdesk_tickets') }} t
left join {{ ref('stg_staff') }} requester
    on t.requested_by_employee_id = requester.staff_id
left join {{ ref('stg_staff') }} assignee
    on t.assigned_technician_id = assignee.staff_id
