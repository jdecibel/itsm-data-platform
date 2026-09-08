select
    asset_id,
    client_id,
    asset_type,
    hostname,
    install_date,
    asset_status
from {{ ref('stg_assets') }}
