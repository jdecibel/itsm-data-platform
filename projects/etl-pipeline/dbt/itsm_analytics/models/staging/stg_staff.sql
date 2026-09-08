select
    staff_id,
    name as staff_name,
    role,
    _ingested_at as loaded_at
from {{ source('raw', 'staff') }}
