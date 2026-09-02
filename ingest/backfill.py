import logging
import os
import time
from datetime import date, timedelta
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://www.cbr-xml-daily.ru/archive/{:%Y/%m/%d}/daily_json.js"
START_DATE = date(2024, 1, 1)
REQUEST_DELAY = 0.5
COMMIT_EVERY = 50

INSERT_SQL = (
    "INSERT INTO raw_daily_rates (rate_date, payload) VALUES (%s, %s) "
    "ON CONFLICT (rate_date) DO UPDATE SET payload = EXCLUDED.payload, fetched_at = now() "
    "WHERE raw_daily_rates.payload -> 'Valute' IS DISTINCT FROM EXCLUDED.payload -> 'Valute' "
    "RETURNING (xmax = 0) AS inserted"
)


def backfill(start_date=START_DATE, end_date=None):
    end_date = end_date or date.today()
    conn = None
    try:
        parsed = urlparse(os.environ["AIRFLOW_CONN_VALUTE_POSTGRES"])
        conn = psycopg2.connect(
            host=os.environ.get("VALUTE_DB_HOST", parsed.hostname),
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432,
        )
        cur = conn.cursor()

        fetched = inserted = updated = unchanged = missing = 0
        d = start_date

        while d <= end_date:
            time.sleep(REQUEST_DELAY)
            response = requests.get(ARCHIVE_URL.format(d), timeout=30)

            if response.status_code == 404:
                missing += 1
                logger.info("Missing %s", d)
                d += timedelta(days=1)
                continue

            response.raise_for_status()
            data = response.json()

            cur.execute(INSERT_SQL, [data["Date"], psycopg2.extras.Json(data)])
            fetched += 1

            if cur.rowcount == 0:
                unchanged += 1             
            elif cur.fetchone()[0]:
                inserted += 1
                logger.info("Inserted %s (%d currencies)", d, len(data.get("Valute", {})))
            else:
                updated += 1
                logger.info("Updated %s (%d currencies)", d, len(data.get("Valute", {})))

            if fetched % COMMIT_EVERY == 0:
                conn.commit()

            d += timedelta(days=1)

        conn.commit()
        cur.close()
        logger.info("Done: %d fetched, %d inserted, %d updated, %d unchanged, %d not published", fetched, inserted, updated, unchanged, missing)

    except Exception:
        logger.exception("Backfill failed")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    backfill()
