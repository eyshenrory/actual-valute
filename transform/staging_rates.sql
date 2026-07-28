INSERT INTO staging_rates (rate_date, char_code, nominal, value, previous)
SELECT
    rate_date,
    kv.key                          as char_code,
    (kv.value ->> 'Nominal')::int   as nominal,
    (kv.value ->> 'Value')::numeric as value,
    (kv.value ->> 'Previous')::numeric as previous
FROM raw_daily_rates, jsonb_each(payload -> 'Valute') AS kv(key, value)
ON CONFLICT (rate_date, char_code) DO UPDATE SET
    nominal  = EXCLUDED.nominal,
    value    = EXCLUDED.value,
    previous = EXCLUDED.previous;