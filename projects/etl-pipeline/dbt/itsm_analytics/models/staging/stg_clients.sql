select
    client_id,
    client_name,
    industry,
    contract_tier,
    _ingested_at as loaded_at
from {{ source('raw', 'clients') }}
