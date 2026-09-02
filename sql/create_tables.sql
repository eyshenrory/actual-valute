CREATE TABLE IF NOT EXISTS raw_daily_rates (
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  rate_date DATE PRIMARY KEY,
  payload JSONB NOT NULL
);