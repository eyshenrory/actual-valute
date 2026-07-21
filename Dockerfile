FROM apache/airflow:3.3.0
ADD requirements.txt .
RUN pip install apache-airflow==3.3.0 -r requirements.txt
