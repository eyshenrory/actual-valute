import logging
import os
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras
import requests

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)
   
logger = logging.getLogger(__name__)

def fetch_and_land():
    conn = None
    try:
        conn_uri = os.environ["AIRFLOW_CONN_VALUTE_POSTGRES"]
        parsed = urlparse(conn_uri)

        logger.info("Fetching rates from CBR API")
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
        response.raise_for_status()
        data = response.json()

        conn = psycopg2.connect(
            host=os.environ.get("VALUTE_DB_HOST", parsed.hostname),
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO raw_daily_rates (rate_date, payload) VALUES (%s, %s) "
            "ON CONFLICT (rate_date) DO UPDATE SET payload = EXCLUDED.payload",
            [data["Date"], psycopg2.extras.Json(data)]
        )
        conn.commit()
        logger.info("Landed raw payload, %d currencies", len(data.get("Valute", {})))
        cur.close()
    except Exception:
        logger.exception("Ingest failed")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fetch_and_land()