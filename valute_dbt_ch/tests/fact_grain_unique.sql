select
    rate_date,
    char_code,
    count(*) as row_count
from {{ ref('fct_daily_rates') }}
group by rate_date, char_code
having count(*) > 1