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

CREATE TABLE IF NOT EXISTS dim_currency (
  currency_key SERIAL PRIMARY KEY,
  cbr_id TEXT NOT NULL UNIQUE,
  num_code TEXT,
  char_code TEXT NOT NULL UNIQUE,
  name TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
  date_key INT PRIMARY KEY,
  full_date DATE NOT NULL UNIQUE,
  year INT, month INT, day INT,
  day_of_week INT,
  is_weekend BOOLEAN
);

CREATE TABLE IF NOT EXISTS fct_daily_rates (
  date_key INT REFERENCES dim_date(date_key),
  currency_key INT REFERENCES dim_currency(currency_key),
  value NUMERIC NOT NULL,
  previous NUMERIC,
  nominal INT NOT NULL,
  rate_per_unit NUMERIC, 
  PRIMARY KEY (date_key, currency_key)
);