import logging
import os

import clickhouse_connect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DDL_PATH = "/opt/airflow/valute/sql/create_clickhouse_tables.sql"


def create_tables(ddl_path=DDL_PATH):
    client = clickhouse_connect.get_client(
        host=os.environ.get("VALUTE_CH_HOST", "localhost"),
        port=int(os.environ.get("VALUTE_CH_PORT", 8123)),
        username=os.environ.get("VALUTE_CH_USER", "admin"),
        password=os.environ.get("VALUTE_CH_PASSWORD", "admin"),
        database="valute",
    )

    with open(ddl_path) as f:
        statements = [s.strip() for s in f.read().split(";") if s.strip()]

    for statement in statements:
        client.command(statement)

    logger.info("Executed %d DDL statements", len(statements))


if __name__ == "__main__":
    create_tables()