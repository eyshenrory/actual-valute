#!/bin/bash
set -e

docker compose up -d 
docker exec -i valute_postgres psql -U admin -d valute < sql/create_tables.sql 
venv/bin/python3 ingest/fetch_and_land.py 
docker exec -i valute_postgres psql -U admin -d valute < transform/staging_rates.sql
