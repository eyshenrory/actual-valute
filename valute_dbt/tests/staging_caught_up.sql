select max(rate_date) as staging_max
from {{ ref('stg_cbr__rates') }}
having max(rate_date) < (
    select (payload ->> 'Date')::date
    from {{ source('cbr', 'raw_daily_rates') }}
    order by rate_date desc
    limit 1
)