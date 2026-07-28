{{ config(
    materialized='incremental',
    unique_key=['rate_date', 'char_code']
)
}}

select
    rate_date,
    kv.value ->> 'ID' as cbr_id,
    kv.key as char_code,
    kv.value ->> 'NumCode' as num_code,
    kv.value ->> 'Name' as name,
    (kv.value ->> 'Nominal')::int as nominal,
    (kv.value ->> 'Value')::numeric as value,
    (kv.value ->> 'Previous')::numeric as previous
from
    {{ source('cbr', 'raw_daily_rates') }}, 
    jsonb_each(payload -> 'Valute') as kv(key, value)
{% if is_incremental() %}
    where rate_date >= (select max(rate_date) from {{ this }}) - interval '3 days'
{% endif %}