{{ config(
    materialized='incremental',
    unique_key=['rate_date', 'char_code']
)
}}

select
    sr.rate_date,
    dc.char_code,
    sr.value,
    sr.previous,
    sr.nominal,
    sr.value / sr.nominal as rate_per_unit
from {{ ref('stg_cbr__rates') }} sr
join {{ ref('dim_currency') }} dc on dc.char_code = sr.char_code
join {{ ref('dim_date') }} dd on dd.full_date  = sr.rate_date
{% if is_incremental() %}
    where sr.rate_date >= (select max(rate_date) from {{ this }}) - interval '3 days'
{% endif %}