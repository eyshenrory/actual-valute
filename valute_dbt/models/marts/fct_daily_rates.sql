{{ config(
    materialized='incremental',
    unique_key=['rate_date', 'char_code']
) }}

select
    rate_date,
    char_code,
    value,
    previous,
    nominal,
    value / nominal as rate_per_unit
from {{ ref('stg_cbr__rates') }}

{% if is_incremental() %}
    where rate_date >= (select max(rate_date) from {{ this }}) - interval '3 days'
{% endif %}