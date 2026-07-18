INSERT INTO staging_rates (rate_date, char_code, nominal, value, previous, source_id)
SELECT
    (payload ->> 'Date')::date AS rate_date,
    kv.key AS char_code,
    (kv.value ->> 'Nominal')::int AS nominal,
    (kv.value ->> 'Value')::numeric AS value,
    (kv.value ->> 'Previous')::numeric AS previous,
    id AS source_id
FROM raw_daily_rates, jsonb_each(payload -> 'Valute') AS kv(key, value)
ON CONFLICT (rate_date, char_code) DO NOTHING;