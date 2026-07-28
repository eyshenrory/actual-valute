CREATE TABLE IF NOT EXISTS raw_daily_rates (
  rate_date DATE PRIMARY KEY,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL
);