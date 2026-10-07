import logging
import os
from datetime import timedelta
from urllib.parse import urlparse

import clickhouse_connect
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

LOAD_WINDOW_DAYS = 3

COLUMNS = [
    "fetched_at",
    "rate_date",
    "cbr_id",
    "char_code",
    "num_code",
    "name",
    "nominal",
    "value",
    "previous"
]

SELECT_SQL = f"""
    SELECT {", ".join(COLUMNS)}
    FROM stg_cbr__rates
    WHERE rate_date >= %s
    ORDER BY rate_date, char_code
"""

MAX_DATE = """
    SELECT greatest(max(rate_date), toDate('2020-01-01'))
    FROM pg_stg_rates
"""


def load_to_clickhouse(window_days=LOAD_WINDOW_DAYS):
    pg_conn = None
    try:
        parsed = urlparse(os.environ["AIRFLOW_CONN_VALUTE_POSTGRES"])

        pg_conn = psycopg2.connect(
            host=os.environ.get("VALUTE_DB_HOST", parsed.hostname),
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432,
        )

        ch = clickhouse_connect.get_client(
            host=os.environ.get("VALUTE_CH_HOST", "localhost"),
            port=int(os.environ.get("VALUTE_CH_PORT", 8123)),
            username=os.environ.get("VALUTE_CH_USER", "admin"),
            password=os.environ.get("VALUTE_CH_PASSWORD", "admin"),
            database="valute",
        )

        cutoff = ch.query(MAX_DATE).result_rows[0][0] - timedelta(days=window_days)
        cur = pg_conn.cursor()
        cur.execute(SELECT_SQL, (cutoff,))
        rows = cur.fetchall()
        cur.close()

        if not rows:
            logger.warning("No rows in Postgres since %s — nothing to load", cutoff)
            return

        logger.info("Read %d rows from Postgres since %s", len(rows), cutoff)

        ch.insert("pg_stg_rates", rows, column_names=COLUMNS)
        logger.info("Loaded %d rows into ClickHouse", len(rows))

    except Exception:
        logger.exception("Load to ClickHouse failed")
        raise
    finally:
        if pg_conn:
            pg_conn.close()


if __name__ == "__main__":
    load_to_clickhouse()
