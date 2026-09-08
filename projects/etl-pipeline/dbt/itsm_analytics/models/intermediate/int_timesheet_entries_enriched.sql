select
    ts.timesheet_id,
    ts.project_id,
    p.project_name,
    p.client_id,
    c.client_name,
    ts.employee_id,
    emp.staff_name as employee_name,
    ts.work_date,
    ts.hours,
    ts.billable,
    ts.task_description
from {{ ref('stg_timesheets') }} ts
left join {{ ref('stg_projects') }} p on ts.project_id = p.project_id
left join {{ ref('stg_clients') }} c on p.client_id = c.client_id
left join {{ ref('stg_staff') }} emp on ts.employee_id = emp.staff_id
