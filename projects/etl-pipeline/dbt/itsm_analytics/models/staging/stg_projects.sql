select
    project_id,
    client_id,
    project_name,
    start_date,
    end_date,
    contract_type,
    project_manager_id,
    status as project_status,
    _ingested_at as loaded_at
from {{ source('raw', 'projects') }}
