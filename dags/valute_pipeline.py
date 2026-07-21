from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="valute_pipeline",
    schedule="0 09 * * *",
    start_date=datetime(2026, 7, 1),
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