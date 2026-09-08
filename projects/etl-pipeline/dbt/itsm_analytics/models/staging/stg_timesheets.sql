select
    timesheet_id,
    project_id,
    employee_id,
    work_date,
    hours,
    billable,
    task_description,
    _ingested_at as loaded_at
from {{ source('raw', 'timesheets') }}
