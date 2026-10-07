select rate_date as "Date", rate_per_unit as "Rate"
from fct_daily_rates
where char_code = {char_code:String}
order by rate_date
