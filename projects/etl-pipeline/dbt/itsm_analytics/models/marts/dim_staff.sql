select
    staff_id,
    staff_name,
    role,
    -- The 40-person cross-domain pool (Helpdesk Technician, Field Engineer,
    -- Project Manager, Account Manager) gets assigned to actual work; the
    -- 900 plain Employee-role staff only ever appear as helpdesk requesters.
    role != 'Employee' as is_technician
from {{ ref('stg_staff') }}
