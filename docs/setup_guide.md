# Setup Guide

## Local Python

```powershell
python scripts/run_pipeline.py
python scripts/simulate_stream.py
python -m unittest discover -s tests
```

The local pipeline does not require external services. It uses the Python standard library for generation, ETL, quality checks, and streaming simulation.

## Optional Dependencies

```powershell
python -m pip install -r requirements.txt
```

Install optional dependencies when using dbt, BigQuery, Kafka clients, or pytest.

## Docker

```powershell
docker compose up loan-intelligence
```

To start Kafka or Airflow services, include those services explicitly:

```powershell
docker compose up kafka zookeeper
docker compose up airflow-postgres airflow-webserver airflow-scheduler
```

Airflow may require database initialization before first use in a production-grade setup.

## BigQuery

1. Create or select a GCP project.
2. Create a service account with BigQuery permissions.
3. Copy `dbt/profiles.yml.example` to your dbt profiles directory and update project, dataset, and keyfile values.
4. Run the DDL in `sql/bigquery/ddl.sql`.
5. Run dbt models from the `dbt/` directory.
