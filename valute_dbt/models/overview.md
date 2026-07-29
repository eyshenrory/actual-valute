{% docs __overview__ %}

# Actual Valute

Пайплайн курсов валют ЦБ РФ.

Слои:
- **source** — `raw_daily_rates`, сырые ответы API
- **staging** — `stg_cbr__rates`, распакованный JSON
- **marts** — схема «Звезда»: `fct_daily_rates`, `dim_currency`, `dim_date`

{% enddocs %}