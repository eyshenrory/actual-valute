{{ config(
    materialized='incremental',
    unique_key=['rate_date', 'char_code'],
    incremental_strategy='delete+insert',
    order_by=['rate_date', 'char_code']
) }}

select
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

limit 1 by rate_date, char_code