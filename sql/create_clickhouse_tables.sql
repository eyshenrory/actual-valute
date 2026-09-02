CREATE TABLE IF NOT EXISTS valute.pg_stg_rates
(
    fetched_at DateTime64(6, 'Europe/Moscow'),
    rate_date Date,
    cbr_id String,
    char_code String,
    num_code String,
    name String,
    nominal Int32,
    value Decimal(18, 4),
    previous Nullable(Decimal(18, 4))
)
ENGINE = ReplacingMergeTree(fetched_at)
ORDER BY (char_code, rate_date);