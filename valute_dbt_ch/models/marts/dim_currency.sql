{{ config(materialized='table') }}

select distinct on (char_code)
    cbr_id,
    num_code,
    char_code,
    name
from {{ source('pg', 'pg_stg_rates') }}
order by char_code, rate_date desc