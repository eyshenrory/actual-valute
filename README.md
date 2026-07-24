# Actual Valute

![Tests](https://github.com/eyshenrory/actual-valute/actions/workflows/test.yaml/badge.svg)

Пайплайн данных, который ежедневно получает курсы валют с API
Центрального банка РФ, сохраняет их в исходном виде, затем вставляет в основную таблицу и запускается по расписанию с автоматической
проверкой данных.


## Архитектура
```mermaid
flowchart LR
    A[CBR API] -->|requests| B[ingest]
    B --> C[(raw_daily_rates)]
    C -->|SQL transform| D[(staging_rates)]
    D --> E{guard}
    E -->|pass| F[Queryable data]
    E -->|fail| G[DAG fails]

    subgraph Airflow DAG
        B
        C
        D
        E
    end
```

| Этап        | Процесс                                                                | Расположение                         |
|-------------|---------------------------------------------------------------------------|-----------------------------------|
| Ingest      | Получение курсов валют за день с API ЦБ РФ                               | `ingest/fetch_and_land.py`        |
| Land        | Сохранение ответа в виде JSON-строки                                     | таблица `raw_daily_rates`         |
| Transform   | Разбор JSON в таблицу `staging_rates`                                    | `transform/staging_rates.sql`     |
| Guard       | Явный отказ, если данных мало или они устарели                           | `sql/guard_check.sql`             |
| Orchestrate | Ежедневный запуск ingest → transform → guard                             | DAG Airflow (`dags/valute_pipeline.py`) |


## Технологии

- **Python** — `requests`, `psycopg2`
- **PostgreSQL** — хранение данных
- **Apache Airflow** — оркестрация
- **Docker Compose** — контейнеризация
- **pytest** — тесты 
- **GitHub Actions** — автоматический запуск тестов при каждом push


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


## Тесты

```bash
pip install -r requirements.txt pytest
pytest

```


## Проверка качества данных 

Задача `guard` завершает DAG с ошибкой, если для последней даты выполняется любое из условий:
- Меньше 40 валютных строк за последнюю доступную дату
- Последняя дата (`rate_date`) устарела более чем на 3 дня


## Пример результата

![USD/RUB](serve/usd_trend.png)

График строится скриптом `serve/plot_rates.py` по данным, собранным пайплайном.
