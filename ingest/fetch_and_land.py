import psycopg2
import psycopg2.extras
import requests


def fetch_and_land():
    conn = None
    try:
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
        response.raise_for_status()
        data = response.json()

        conn = psycopg2.connect(
            host="valute-postgres",
            dbname="valute",
            user="admin",
            password="admin",
            port=5432
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