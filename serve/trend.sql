select rate_date as "Date", rate_per_unit as "Rate"
from fct_daily_rates 
where char_code = %s
order by rate_date;