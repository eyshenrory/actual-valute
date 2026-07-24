import matplotlib

matplotlib.use("Agg")  
import os
from urllib.parse import urlparse

import matplotlib.pyplot as plt
import psycopg2

conn_uri = os.environ["AIRFLOW_CONN_VALUTE_POSTGRES"]
parsed = urlparse(conn_uri)

conn = psycopg2.connect(
    host=os.environ.get("VALUTE_DB_HOST", "localhost"),
    dbname=parsed.path.lstrip("/"),
    user=parsed.username,
    password=parsed.password,
    port=parsed.port or 5432
)
cur = conn.cursor()
with open("serve/usd_trend.sql") as f:
    cur.execute(f.read())
rows = cur.fetchall()
dates = [r[0] for r in rows]
values = [r[1] for r in rows]
cur.close()
conn.close()

plt.plot(dates, values, marker="o")
plt.title("USD / RUB")
plt.xlabel("Date")
plt.ylabel("Rate")
plt.grid(True)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("serve/usd_trend.png")
