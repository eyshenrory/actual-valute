{{ config(materialized='table') }}

select
    toDate('2020-01-01') + number as full_date,
    toYear(toDate('2020-01-01') + number) as year,
    toMonth(toDate('2020-01-01') + number) as month,
    toDayOfMonth(toDate('2020-01-01') + number) as day,
    toDayOfWeek(toDate('2020-01-01') + number) as day_of_week,
    toDayOfWeek(toDate('2020-01-01') + number) >= 6 as is_weekend
from numbers(4018)