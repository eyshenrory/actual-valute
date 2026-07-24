import os
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras
import requests


def fetch_and_land():
    conn = None
    try:
        conn_uri = os.environ["AIRFLOW_CONN_VALUTE_POSTGRES"]
        parsed = urlparse(conn_uri)

        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
        response.raise_for_status()
        data = response.json()

        conn = psycopg2.connect(
            host=parsed.hostname,
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO raw_daily_rates (payload) VALUES (%s)",
            [psycopg2.extras.Json(data)]
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Ingest failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fetch_and_land()