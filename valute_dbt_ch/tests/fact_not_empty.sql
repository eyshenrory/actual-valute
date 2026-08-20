select count(*) as row_count
from {{ ref('fct_daily_rates') }}
having count(*) = 0