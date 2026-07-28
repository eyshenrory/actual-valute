select
    (select count(*) < 20 from stg_cbr__rates
     where rate_date = (select max(rate_date) from stg_cbr__rates))
    or
    (select (payload ->> 'Date')::date > (select max(rate_date) from stg_cbr__rates)
     from raw_daily_rates order by rate_date desc limit 1)
    or
    (
        (select count(*) from stg_cbr__rates
         where rate_date = (select max(rate_date) from stg_cbr__rates))
        !=
        (select count(*) from fct_daily_rates
         where rate_date = (select max(rate_date) from fct_daily_rates))
    )
    as pipeline_failed;