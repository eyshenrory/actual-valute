# Actual Valute

![Tests](https://github.com/eyshenrory/actual-valute/actions/workflows/test.yaml/badge.svg)

Пайплайн данных, который ежедневно получает курсы валют с API
Центрального банка РФ, сохраняет их в исходном виде, затем вставляет в основную таблицу и запускается по расписанию с автоматической
проверкой данных.

## Архитектура

```
CBR API  →  ingest  →  land  →  transform  →  guard
                       (raw)    (staging)    (checks)
```

| Этап        | Процесс                                                                | Расположение                         |
|-------------|---------------------------------------------------------------------------|-----------------------------------|
| Ingest      | Получение курсов валют за день с API ЦБ РФ                               | `ingest/fetch_and_land.py`        |
| Land        | Сохранение ответа в виде JSON-строки                                     | таблица `raw_daily_rates`         |
| Transform   | Разбор JSON в типизированные построчные данные по каждой валюте          | `transform/staging_rates.sql`     |
| Guard       | Явный отказ, если данных мало или они устарели                           | `sql/guard_check.sql`             |
| Orchestrate | Ежедневный запуск ingest → transform → guard                             | DAG Airflow (`dags/valute_pipeline.py`) |


## Технологии

- **Python** — `requests`, `psycopg2`
- **PostgreSQL 18** — хранение данных
- **Apache Airflow 3.3** — оркестрация
- **Docker Compose** — контейнеризация
- **pytest** — тесты 
- **GitHub Actions** — автоматический запуск тестов при каждом push и pull


## Установка и запуск


1. **Клонировать репозиторий, создать нужные директории:**
   ```bash
   mkdir -p ./dags ./logs ./plugins ./config
   ```

2. **Переменные в `.env`**:
   ```bash
   echo -e "AIRFLOW_UID=$(id -u)" > .env
   ```
   Определить подключение к Postgres, которое будет использовать Airflow:
   ```
   AIRFLOW_CONN_VALUTE_POSTGRES=postgres://admin:admin@valute-postgres:5432/valute
   ```

3. **Сборка:**
   ```bash
   docker compose build
   docker compose up airflow-init
   docker compose up -d
   ```

4. **Airflow** на [http://localhost:8080](http://localhost:8080)
   (логин `airflow` / пароль `airflow`) Запускается ежедневно в 12:00 по МСК.

## Проверка результата

```bash
docker exec -it valute_postgres psql -U admin -d valute
```
```sql
SELECT rate_date, COUNT(*) FROM staging_rates GROUP BY rate_date ORDER BY rate_date;
```

## Тесты

```bash
pip install -r requirements.txt pytest
pytest
```

## Проверка качества данных 

Задача `guard` завершает DAG с ошибкой, если для последней даты выполняется любое из условий:
- Меньше 40 валютных строк за последнюю доступную дату
- Последняя дата (`rate_date`) устарела более чем на 3 дня
