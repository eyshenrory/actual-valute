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
    "ON CONFLICT (rate_date) DO UPDATE SET payload = EXCLUDED.payload"
)


def backfill(start_date=START_DATE, end_date=None):
    end_date = end_date or date.today()
    conn = None
    try:
        parsed = urlparse(os.environ["AIRFLOW_CONN_VALUTE_POSTGRES"])
        conn = psycopg2.connect(
            host=parsed.hostname,
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432,
        )
        cur = conn.cursor()

        cur.execute("SELECT rate_date FROM raw_daily_rates")
        existing = {row[0] for row in cur.fetchall()}
        logger.info("Already have %d dates", len(existing))

        landed = skipped = missing = 0
        d = start_date

        while d <= end_date:
            if d in existing:
                skipped += 1
                logger.info("Skipped %s", d)
                d += timedelta(days=1)
                continue

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
            landed += 1
            logger.info("Landed %s (%d currencies)", d, len(data.get("Valute", {})))

            if landed % COMMIT_EVERY == 0:
                conn.commit()

            d += timedelta(days=1)

        conn.commit()
        cur.close()
        logger.info("Done: %d landed, %d skipped, %d not published", landed, skipped, missing)

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