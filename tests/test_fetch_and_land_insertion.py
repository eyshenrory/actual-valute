from unittest.mock import MagicMock, patch

import ingest.fetch_and_land as fal


def test_fetch_and_land_insertion(monkeypatch):
    monkeypatch.setenv("AIRFLOW_CONN_VALUTE_POSTGRES", "postgres://admin:admin@localhost:5432/valute")

    fake_api_response = {"Date": "2026-07-24T11:30:00+03:00", "Valute": {"USD": {"Value": 78.0}}}

    with patch("ingest.fetch_and_land.requests.get") as mock_get, \
         patch("ingest.fetch_and_land.psycopg2.connect") as mock_connect:

        mock_get.return_value.json.return_value = fake_api_response
        mock_get.return_value.raise_for_status.return_value = None

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        fal.fetch_and_land()

        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "INSERT INTO raw_daily_rates" in args[0]
        assert args[1][0].adapted == fake_api_response