{{ config(materialized='table') }}

select 
    g.d::date as full_date, 
    extract(year from g.d)::int as year, extract(month from g.d)::int as month, extract(day from g.d)::int as day, 
    extract(isodow from g.d)::int as day_of_week,
    extract(isodow from g.d)::int >= 6 as is_weekend
from generate_series('2020-01-01'::date, '2030-12-31'::date, '1 day'::interval) as g(d)