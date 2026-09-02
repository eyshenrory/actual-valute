{{ config(
    materialized='incremental',
    unique_key=['char_code', 'rate_date'],
    incremental_strategy='delete+insert',
    order_by=['char_code', 'rate_date']
) }}

select
    fetched_at,
    rate_date,
    char_code,
    value,
    previous,
    nominal,
    value / nominal as rate_per_unit
from {{ source('pg', 'pg_stg_rates') }}

{% if is_incremental() %}
    where rate_date >= (select max(rate_date) from {{ this }}) - INTERVAL 3 DAY
{% endif %}

order by fetched_at desc, value desc 
limit 1 by rate_date, char_code