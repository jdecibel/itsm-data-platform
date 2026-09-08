-- Grain: one row per timesheet entry. Sourced straight from staging, not
-- int_timesheet_entries_enriched — no derived measure exists at this grain
-- (hours/billable are already exactly what the source records), so there's
-- nothing to gain from depending on the wider, name-joined intermediate
-- model just to discard its extra columns. That model remains the flattened
-- alternative for ad-hoc querying.
select
    timesheet_id,
    work_date,
    project_id,
    employee_id,
    hours,
    billable,
    task_description
from {{ ref('stg_timesheets') }}
