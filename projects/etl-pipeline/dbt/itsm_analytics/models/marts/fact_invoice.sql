-- Grain: one row per invoice. Sourced from staging directly, same reasoning
-- as fact_timesheet_entry — no derived measure exists at invoice grain
-- (int_project_financials aggregates invoices up to project grain, which is
-- a different fact's job, not this one's).
select
    invoice_id,
    invoice_date,
    project_id,
    client_id,
    amount,
    invoice_status
from {{ ref('stg_invoices') }}
