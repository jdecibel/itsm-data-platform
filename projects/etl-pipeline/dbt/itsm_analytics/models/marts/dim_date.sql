-- 2023-01-01 through 2026-12-31 — covers every date actually observed in the
-- source data with margin (projects.end_date's real max lands around
-- 2025-12; the +1 year of headroom means this doesn't need revisiting every
-- time the synthetic data's date range shifts). date_spine's end_date bound
-- is exclusive, hence 2027-01-01.
with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2023-01-01' as date)",
        end_date="cast('2027-01-01' as date)"
    ) }}
)

select
    date_day,
    extract(year from date_day)::int as year,
    extract(month from date_day)::int as month,
    extract(day from date_day)::int as day,
    extract(quarter from date_day)::int as quarter,
    to_char(date_day, 'Day') as day_name,
    to_char(date_day, 'Month') as month_name,
    -- Postgres EXTRACT(DOW ...): 0 = Sunday, 6 = Saturday
    (extract(dow from date_day) in (0, 6)) as is_weekend
from spine
