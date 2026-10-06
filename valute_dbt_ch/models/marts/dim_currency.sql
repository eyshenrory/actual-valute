{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key=['char_code'],
    engine='MergeTree',
    order_by=['char_code']
) }}

with batch as (
    select
        char_code,
        argMax((cbr_id, num_code, name), (fetched_at, rate_date)) as attrs,
        min(rate_date) as first_seen_date,
        max(rate_date) as last_seen_date
    from {{ source('pg', 'pg_stg_rates') }}
    group by char_code
)

select
    b.char_code as char_code,
    tupleElement(b.attrs, 1) as cbr_id,
    tupleElement(b.attrs, 2) as num_code,
    tupleElement(b.attrs, 3) as name,
{% if is_incremental() %}
    if(t.char_code = '', b.first_seen_date, least(b.first_seen_date, t.first_seen_date)) as first_seen_date,
    if(t.char_code = '', b.last_seen_date, greatest(b.last_seen_date, t.last_seen_date)) as last_seen_date
from batch as b
left join {{ this }} as t on t.char_code = b.char_code
{% else %}
    b.first_seen_date as first_seen_date,
    b.last_seen_date as last_seen_date
from batch as b
{% endif %}
