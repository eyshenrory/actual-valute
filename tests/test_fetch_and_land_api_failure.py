from unittest.mock import MagicMock, patch

import pytest

import ingest.fetch_and_land as fal


def test_fetch_and_land_api_failure(monkeypatch):
    monkeypatch.setenv("AIRFLOW_CONN_VALUTE_POSTGRES", "postgres://admin:admin@localhost:5432/valute")
    with patch("ingest.fetch_and_land.requests.get") as mock_get, \
         patch("ingest.fetch_and_land.psycopg2.connect") as mock_connect:

        mock_get.side_effect = Exception("API Failure")

        with pytest.raises(Exception, match="API Failure"):
            fal.fetch_and_land()

        mock_connect.assert_not_called()