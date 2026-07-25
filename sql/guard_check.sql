SELECT
    (SELECT COUNT(*) < 40 FROM staging_rates
     WHERE rate_date = (SELECT MAX(rate_date) FROM staging_rates))
    OR
    (SELECT (MAX(rate_date) + INTERVAL '3 days') < CURRENT_DATE FROM staging_rates)
    OR
    ( 
        (SELECT COUNT(*) FROM staging_rates
        WHERE rate_date = (SELECT MAX(rate_date) FROM staging_rates))
        !=
        (SELECT COUNT(*) FROM fct_daily_rates
        WHERE date_key = (SELECT MAX(date_key) FROM fct_daily_rates))
    )
    AS pipeline_failed;