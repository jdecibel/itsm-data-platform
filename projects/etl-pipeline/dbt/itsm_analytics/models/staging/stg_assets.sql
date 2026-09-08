select
    asset_id,
    client_id,
    asset_type,
    hostname,
    install_date,
    status as asset_status,
    _ingested_at as loaded_at
from {{ source('raw', 'assets') }}
