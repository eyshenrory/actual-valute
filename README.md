# Actual Valute

![Tests](https://github.com/eyshenrory/actual-valute/actions/workflows/test.yaml/badge.svg)

Пайплайн данных, который ежедневно получает курсы валют с API Центрального
банка РФ, сохраняет их в исходном виде в PostgreSQL, переносит в ClickHouse и
через dbt строит там схему "Звезда". Запускается по расписанию с
автоматическими проверками качества данных.

## Архитектура

```mermaid
flowchart LR
    A[CBR API] -->|requests| B[ingest]
    B --> C[(raw_daily_rates)]
    C -->|dbt| D[(stg_cbr__rates)]
    D --> T1{dbt test}
    T1 -->|pass| L[load_ch]
    L --> S[(pg_stg_rates)]
    S -->|dbt| E[(dim_currency)]
    S -->|dbt| G[(fct_daily_rates)]
    F[(dim_date)] -.-> |join| G
    E -.-> |join| G
    G --> H{dbt test}
    H -->|pass| I[Queryable star schema]
    H -->|fail| J[DAG fails]
    T1 -->|fail| J

    subgraph PostgreSQL
        C
        D
    end

    subgraph ClickHouse
        S
        E
        F
        G
    end
```

| Этап        | Процесс                                                        | Расположение                              |
|-------------|----------------------------------------------------------------|-------------------------------------------|
| Ingest      | Получение курсов валют за день с API ЦБ РФ                     | `ingest/fetch_and_land.py`                |
| Land        | Сохранение ответа в исходном виде (JSONB, PostgreSQL)          | таблица `raw_daily_rates`                 |
| Staging     | Разбор JSON в типизированные строки (PostgreSQL)               | `valute_dbt/models/staging/`              |
| Load        | Перенос staging в ClickHouse                                   | `ingest/load_to_clickhouse.py`, `sql/create_clickhouse_tables.sql` |
| Marts       | Построение схемы "Звезда" (ClickHouse)                         | `valute_dbt_ch/models/marts/`             |
| Tests       | Проверки уникальности, гранулярности, ссылочной целостности и актуальности | `valute_dbt/tests/`, `valute_dbt_ch/models/marts/schema.yml`, `valute_dbt_ch/tests/` |
| Orchestrate | Ежедневный запуск пайплайна                                    | `dags/valute_pipeline.py`                 |

### Решения по моделированию

**Слой сырых данных.** `raw_daily_rates` содержит неизменённый
JSON-ответ от API. Ключ — `rate_date` (натуральный), одна строка на одну дату публикации.

**Схема "Звезда" без суррогатных ключей.** Измерения соединяются с таблицей
фактов по натуральным ключам (`char_code`, `full_date`).

**`nominal` хранится в таблице фактов, а не в измерении.** 
`dim_currency` реализовано как SCD Type 1, поэтому при деноминации историческое
значение `nominal` было бы потеряно. `rate_per_unit` (`value / nominal`)
делает курсы разных валют сопоставимыми.

**Инкрементальные модели.** При каждом запуске берутся строки с
`rate_date >= max(rate_date) - 3 дня`, где `max(rate_date)` — из самой модели,
а не текущая дата. Верхней границы у окна нет: после простоя пайплайна
подхватываются все новые даты, сколько бы их ни было. Три дня назад от
последней загруженной даты пересчитываются заново, чтобы подхватить
исправления курсов на стороне ЦБ. Так устроены `stg_cbr__rates` и
`fct_daily_rates`. Перенос в ClickHouse (`ingest/load_to_clickhouse.py`)
устроен так же: окно отсчитывается от `max(rate_date)` в `pg_stg_rates`.

**`dim_currency` — накопительный справочник.** Инкрементальная модель со
стратегией `delete+insert` по `char_code`: перезаписываются только валюты,
пришедшие в текущем прогоне, а выбывшие (например, BGN после перехода Болгарии
на евро) остаются, чтобы у исторических фактов не появлялись сироты.
`first_seen_date` и `last_seen_date` сливаются с уже записанными значениями,
поэтому пересоздание staging не теряет историю.

**Дубли в ClickHouse.** `pg_stg_rates` — `ReplacingMergeTree(fetched_at)`:
повторная загрузка окна создаёт дубли, которые движок схлопывает в фоне, в
неопределённый момент. Поэтому гранулярность факта обеспечивает модель
(`limit 1 by rate_date, char_code` + `delete+insert`), а проверяет singular-тест
`fact_grain_unique`.

## Технологии

- **Python** — `requests`, `psycopg2`, `clickhouse-connect`
- **PostgreSQL** — сырой слой и staging
- **ClickHouse** — аналитическое хранилище, схема "Звезда"
- **dbt** — преобразования, тесты данных, документация
- **Apache Airflow** — оркестрация
- **Docker Compose** — контейнеризация
- **pytest** — модульные тесты
- **GitHub Actions** — автоматический запуск тестов при каждом push

## Установка и запуск

1. **Клонировать репозиторий, создать нужные директории:**
   ```bash
   mkdir -p ./dags ./logs ./plugins ./config
   ```

2. **Переменные в `.env`:**
   ```bash
   echo -e "AIRFLOW_UID=$(id -u)" > .env
   ```
   Добавить ключ шифрования подключений Airflow:
   ```bash
   docker run --rm python:3.12-slim bash -c \
     "pip install cryptography -q && python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
   ```
   Итоговый `.env`:
   ```
   AIRFLOW_UID=1000
   FERNET_KEY=<сгенерированный ключ>
   AIRFLOW_CONN_VALUTE_POSTGRES=postgres://admin:admin@valute-postgres:5432/valute
   ```

3. **Сборка и запуск:**
   ```bash
   docker compose build
   docker compose up -d
   ```

4. **Airflow** на [http://localhost:8080](http://localhost:8080)
   (логин `airflow` / пароль `airflow`). DAG `valute_pipeline` запускается
   ежедневно в 12:00 по МСК.

5. **Загрузка истории (опционально):**
   ```bash
   VALUTE_DB_HOST=localhost python3 ingest/backfill.py
   ```
   Скрипт обходит архив ЦБ РФ по датам, пропуская уже загруженные и дни без
   публикации (выходные, праздники).

## Тесты

Модульные тесты Python (внешние вызовы замоканы, БД и сеть не требуются):

```bash
pip install -r requirements.txt pytest
pytest
```

Тесты данных dbt (PostgreSQL и ClickHouse):

```bash
cd valute_dbt && DBT_PROFILES_DIR=. dbt test
cd ../valute_dbt_ch && DBT_PROFILES_DIR=. dbt test
```

## Проверка качества данных

`dbt test` проверяет:
- уникальность и заполненность ключей измерений и фактов;
- гранулярность факта: одна строка на валюту и дату;
- ссылочную целостность: каждая валюта в фактах есть в справочнике;
- актуальность: слой staging не отстаёт от того, что загружено в сырой слой.


## Пример результата

График строится скриптом `serve/plot_rates.py`. По умолчанию валютой является Доллар США. 

![USD/RUB](serve/usd_trend.png)

Опционально валюту можно задать переменной окружения:

```bash
CURRENCY=JPY python3 serve/plot_rates.py
```

![JPY/RUB](serve/jpy_trend.png)

## План выполнения

- [x] Цикл жизни данных: ingest → land → staging → marts
- [x] Оркестрация через Airflow с ежедневным запуском
- [x] Схема "Звезда", преобразования и тесты данных в dbt
- [x] Модульные тесты (pytest) и CI (GitHub Actions)
- [x] Загрузка исторических данных из архива ЦБ РФ
- [x] ClickHouse как аналитическое хранилище
- [ ] BI-дашборд
- [ ] Развёртывание в облаке
