# Actual Valute

![Tests](https://github.com/eyshenrory/actual-valute/actions/workflows/test.yaml/badge.svg)

Пайплайн данных, который ежедневно получает курсы валют с API Центрального
банка РФ, сохраняет их в исходном виде, через dbt преобразует в схему "Звезда" 
и запускается по расписанию с автоматическими проверками качества данных.

## Архитектура

```mermaid
flowchart LR
    A[CBR API] -->|requests| B[ingest]
    B --> C[(raw_daily_rates)]
    C -->|dbt| D[(stg_cbr__rates)]
    D -->|dbt| E[(dim_currency)]
    F[(dim_date)] -.-> |join| G
    D -->|dbt| G[(fct_daily_rates)]
    E -.-> |join| G
    G --> H{dbt test}
    H -->|pass| I[Queryable star schema]
    H -->|fail| J[DAG fails]

    subgraph Airflow DAG
        B
        C
        D
        E
        F
        G
        H
    end
```

| Этап        | Процесс                                                        | Расположение                              |
|-------------|----------------------------------------------------------------|-------------------------------------------|
| Ingest      | Получение курсов валют за день с API ЦБ РФ                     | `ingest/fetch_and_land.py`                |
| Land        | Сохранение ответа в исходном виде (JSONB)                      | таблица `raw_daily_rates`                 |
| Staging     | Разбор JSON в типизированные строки                            | `valute_dbt/models/staging/`              |
| Marts       | Построение схемы "Звезда"                                      | `valute_dbt/models/marts/`                |
| Tests       | Проверки уникальности, ссылочной целостности и актуальности    | `valute_dbt/models/marts/schema.yml`, `valute_dbt/tests/` |
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

**Инкрементальные модели.** Окно пересчёта привязано к `max(rate_date)` самой
модели, а не к текущей дате — это гарантирует, что пропуски в данных
(выходные, праздники, простой пайплайна) не будут пропущены при следующем
запуске.

## Технологии

- **Python** — `requests`, `psycopg2`
- **PostgreSQL** — хранение данных
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

Тесты данных dbt:

```bash
cd valute_dbt
DBT_PROFILES_DIR=. dbt test
```

## Проверка качества данных

`dbt test` проверяет:
- уникальность и заполненность ключей измерений и фактов;
- ссылочную целостность: каждая валюта в фактах есть в справочнике;
- актуальность: слой staging не отстаёт от того, что загружено в сырой слой.


## Пример результата

![USD/RUB](serve/usd_trend.png)

График строится скриптом `serve/plot_rates.py`. По умолчанию валютой является Доллар США. 

![JPY/RUB](serve/jpy_trend.png)

Опционально валюту можно задать переменной окружения:

```bash
CURRENCY=JPY python3 serve/plot_rates.py
```


## План выполнения

- [x] Цикл жизни данных: ingest → land → staging → marts
- [x] Оркестрация через Airflow с ежедневным запуском
- [x] Схема "Звезда", преобразования и тесты данных в dbt
- [x] Модульные тесты (pytest) и CI (GitHub Actions)
- [x] Загрузка исторических данных из архива ЦБ РФ
- [ ] ClickHouse как аналитическое хранилище
- [ ] BI-дашборд
- [ ] Развёртывание в облаке
