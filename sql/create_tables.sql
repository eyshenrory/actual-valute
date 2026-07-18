CREATE TABLE IF NOT EXISTS raw_daily_rates (
  id SERIAL PRIMARY KEY,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS staging_rates (
    id SERIAL PRIMARY KEY,
    rate_date DATE NOT NULL,
    char_code TEXT NOT NULL, 
    nominal INT NOT NULL,
    value NUMERIC NOT NULL,
    previous NUMERIC,
    source_id INT REFERENCES raw_daily_rates(id),
    UNIQUE (rate_date, char_code)
);