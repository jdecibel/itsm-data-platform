select
    project_id,
    client_id,
    project_name,
    start_date,
    end_date,
    contract_type,
    project_manager_id,
    project_status
from {{ ref('stg_projects') }}
