from datetime import timedelta

import pendulum
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sdk import dag, task


@dag(
    dag_id="valute_pipeline",
    start_date=pendulum.datetime(2026, 7, 1, tz="Europe/Moscow"),
    schedule="0 12 * * *",
    default_args = {
        "retries": 3,
        "retry_delay": timedelta(seconds=5),
    },
    catchup=False,
    template_searchpath=["/opt/airflow/valute"],
)
def ProcessValute():
    create_tables = SQLExecuteQueryOperator(
        task_id="create_tables",
        conn_id="valute_postgres",
        sql="sql/create_tables.sql",
    )
    ingest = BashOperator(
        task_id="ingest",
        bash_command="python /opt/airflow/valute/ingest/fetch_and_land.py",
        retry_delay=timedelta(minutes=30),
    )
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/valute/valute_dbt && DBT_PROFILES_DIR=. VALUTE_DB_HOST=valute-postgres dbt run",
    )
    dbt_test = BashOperator(
            task_id="dbt_test",
            bash_command="cd /opt/airflow/valute/valute_dbt && DBT_PROFILES_DIR=. VALUTE_DB_HOST=valute-postgres dbt test",
            retries=0,
        )
    create_tables >> ingest >> dbt_run >> dbt_test
dag = ProcessValute()