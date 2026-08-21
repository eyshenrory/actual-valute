CREATE TABLE IF NOT EXISTS valute.pg_stg_rates
(
    rate_date Date,
    cbr_id String,
    char_code String,
    num_code String,
    name String,
    nominal Int32,
    value Decimal(18, 4),
    previous Nullable(Decimal(18, 4))
)
ENGINE = ReplacingMergeTree
ORDER BY (rate_date, char_code);