SELECT rate_date AS "Date", ROUND(value / nominal, 1) AS "USD Rate"
FROM staging_rates
WHERE char_code = 'USD'
ORDER BY rate_date;
