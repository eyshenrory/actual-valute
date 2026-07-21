import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="valute_pipeline",
    schedule="0 12 * * *",
    start_date=pendulum.datetime(2026, 7, 1, tz="Europe/Moscow"),
    catchup=False,
) as dag:
    
    ingest = BashOperator(
        task_id="ingest",
        bash_command="python /opt/airflow/valute/ingest/fetch_and_land.py"
    )
     
    transform = BashOperator(
        task_id="transform",
        bash_command="PGPASSWORD=admin psql -h valute-postgres -U admin -d valute -f /opt/airflow/valute/transform/staging_rates.sql"
    )

    ingest >> transform