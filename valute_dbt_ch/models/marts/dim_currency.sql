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

{% if is_incremental() %}
select *
from batch
where last_seen_date = rate_date
{% endif %}