INSERT INTO dim_currency (cbr_id, num_code, char_code, name)
SELECT DISTINCT ON (kv.value ->> 'ID')
    kv.value ->> 'ID' AS cbr_id,
    kv.value ->> 'NumCode' AS num_code,
    kv.value ->> 'CharCode' AS char_code,
    kv.value ->> 'Name' AS name
FROM raw_daily_rates, jsonb_each(payload -> 'Valute') AS kv(key, value)
ORDER BY kv.value ->> 'ID', raw_daily_rates.rate_date DESC
ON CONFLICT (cbr_id) DO UPDATE SET 
    num_code = EXCLUDED.num_code,
    char_code = EXCLUDED.char_code,
    name = EXCLUDED.name;

INSERT INTO dim_date (date_key, full_date, year, month, day, day_of_week, is_weekend)
SELECT 
    TO_CHAR(g.d, 'YYYYMMDD')::int,
    g.d::date, 
    EXTRACT(YEAR FROM g.d)::int, EXTRACT(MONTH FROM g.d)::int, EXTRACT(DAY FROM g.d)::int, 
    EXTRACT(ISODOW FROM g.d)::int,
    EXTRACT(ISODOW FROM g.d)::int >= 6
FROM generate_series('2020-01-01'::date, '2030-12-31'::date, '1 day'::interval) AS g(d)
ON CONFLICT (date_key) DO NOTHING;

INSERT INTO fct_daily_rates (date_key, currency_key, value, previous, nominal, rate_per_unit)
SELECT
    dd.date_key,
    dc.currency_key,
    sr.value,
    sr.previous,
    sr.nominal,
    sr.value / sr.nominal
FROM staging_rates sr
JOIN dim_currency dc ON dc.char_code = sr.char_code
JOIN dim_date   dd ON dd.full_date  = sr.rate_date
-- WHERE sr.rate_date >= CURRENT_DATE - INTERVAL '3 days'
ON CONFLICT (date_key, currency_key) DO UPDATE SET
    value         = EXCLUDED.value,
    previous      = EXCLUDED.previous,
    nominal       = EXCLUDED.nominal,
    rate_per_unit = EXCLUDED.rate_per_unit;