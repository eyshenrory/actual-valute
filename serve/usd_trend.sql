SELECT dd.full_date AS "Date", fdr.rate_per_unit AS "USD Rate"
FROM fct_daily_rates fdr
JOIN dim_date dd ON fdr.date_key = dd.date_key
JOIN dim_currency dc ON fdr.currency_key = dc.currency_key
WHERE dc.char_code = %s
ORDER BY dd.full_date;
