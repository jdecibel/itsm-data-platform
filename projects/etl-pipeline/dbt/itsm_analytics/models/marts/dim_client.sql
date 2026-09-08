select
    client_id,
    client_name,
    industry,
    contract_tier
from {{ ref('stg_clients') }}
