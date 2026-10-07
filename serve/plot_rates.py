import matplotlib

matplotlib.use("Agg")
import os

import clickhouse_connect
import matplotlib.pyplot as plt

client = clickhouse_connect.get_client(
    host=os.environ.get("VALUTE_CH_HOST", "localhost"),
    port=int(os.environ.get("VALUTE_CH_PORT", 8123)),
    username=os.environ.get("VALUTE_CH_USER", "admin"),
    password=os.environ.get("VALUTE_CH_PASSWORD", "admin"),
    database="valute",
)

char_code = os.environ.get("CURRENCY", "USD")
with open("serve/trend.sql") as f:
    rows = client.query(f.read(), parameters={"char_code": char_code}).result_rows

dates = [r[0] for r in rows]
values = [r[1] for r in rows]
client.close()

plt.plot(dates, values)
plt.title(f"{char_code} / RUB")
plt.xlabel("Date")
plt.ylabel("Rate")
plt.grid(True)
plt.gcf().autofmt_xdate()
plt.tight_layout()
plt.savefig(f"serve/{char_code.lower()}_trend.png")
