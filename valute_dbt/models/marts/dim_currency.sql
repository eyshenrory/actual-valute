{{ config(materialized='table') }}

select distinct on (char_code)
    cbr_id,
    num_code,
    char_code,
    name
from {{ ref('stg_cbr__rates') }}
order by char_code, rate_date desc