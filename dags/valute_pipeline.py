import pendulum
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import dag, task


@dag(
    dag_id="valute_pipeline",
    schedule="0 12 * * *",
    start_date=pendulum.datetime(2026, 7, 1, tz="Europe/Moscow"),
    catchup=False,
    template_searchpath=["/opt/airflow/valute"],
)
def ProcessValute():
    ingest = BashOperator(
        task_id="ingest",
        bash_command="python /opt/airflow/valute/ingest/fetch_and_land.py"
    )
    transform = SQLExecuteQueryOperator(
        task_id="transform",
        conn_id="valute_postgres",
        sql="transform/staging_rates.sql",
    )
    @task
    def guard():
        hook = PostgresHook(postgres_conn_id="valute_postgres")
        conn = hook.get_conn()
        cur = conn.cursor()
        with open("/opt/airflow/valute/sql/guard_check.sql") as f:
            cur.execute(f.read())
        pipeline_failed = cur.fetchone()[0]
        cur.close()
        conn.close()
        if pipeline_failed:
            raise ValueError("Guard check failed: row count too low or data is stale")
    ingest >> transform >> guard()
dag = ProcessValute()