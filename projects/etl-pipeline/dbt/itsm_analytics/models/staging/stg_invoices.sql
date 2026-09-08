select
    invoice_id,
    project_id,
    client_id,
    invoice_date,
    amount,
    status as invoice_status,
    _ingested_at as loaded_at
from {{ source('raw', 'invoices') }}
