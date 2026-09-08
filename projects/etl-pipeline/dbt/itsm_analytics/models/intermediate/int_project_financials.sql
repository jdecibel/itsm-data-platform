-- Timesheets and invoices have no row-level link (invoices attach to
-- project_id, not to timesheet lines) — project grain is the only level
-- where these two sub-domains actually share a key, so that's where they're
-- reconciled. Deliberately not fabricating a finer-grained relationship
-- the source data doesn't support (see LEARNING_LOG's Phase 2 A8 decision).

with timesheet_agg as (
    select
        project_id,
        sum(hours) as total_hours,
        sum(hours) filter (where billable) as billable_hours,
        sum(hours) filter (where not billable) as non_billable_hours
    from {{ ref('stg_timesheets') }}
    group by project_id
),

invoice_agg as (
    select
        project_id,
        count(*) as invoice_count,
        sum(amount) as total_invoiced
    from {{ ref('stg_invoices') }}
    group by project_id
)

select
    p.project_id,
    p.project_name,
    p.client_id,
    p.project_status,
    coalesce(t.total_hours, 0) as total_hours,
    coalesce(t.billable_hours, 0) as billable_hours,
    coalesce(t.non_billable_hours, 0) as non_billable_hours,
    coalesce(i.invoice_count, 0) as invoice_count,
    coalesce(i.total_invoiced, 0) as total_invoiced
from {{ ref('stg_projects') }} p
left join timesheet_agg t on p.project_id = t.project_id
left join invoice_agg i on p.project_id = i.project_id
