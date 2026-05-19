# Loan & Customer Intelligence Platform

An implementation for enterprise loan and customer analytics. The project simulates source systems, runs bronze/silver/gold ETL, creates analytical marts, applies data quality checks, and simulates real-time fraud alerts.

## What Is Included

- Deterministic source data generator for customers, loans, repayments, transactions, collections, and fraud alerts.
- Python ETL pipeline that writes bronze, silver, gold, quarantine, and audit log outputs.
- Gold star-schema tables: `fact_loan_disbursement`, `fact_repayments`, `fact_collections`, `fact_transactions`, `dim_customer`, `dim_product`, `dim_branch`, `dim_date`, and `dim_loan_status`.
- BigQuery DDL and Power BI-ready KPI views.
- dbt project skeleton for BigQuery transformations.
- Airflow DAG for scheduled orchestration.
- Kafka-style JSONL streaming simulation for suspicious transaction alerts.
- Tests and documentation.

## Quick Start

From the repository root:

```powershell
python scripts/run_pipeline.py
python scripts/simulate_stream.py
python -m unittest discover -s tests
```

The pipeline writes outputs to:

- `data/source`: simulated source CSV files
- `data/bronze`: raw ingested records with metadata
- `data/silver`: cleaned and standardized records
- `data/gold`: analytical fact and dimension tables
- `data/quarantine`: rejected records with error reasons
- `logs/etl_runs`: audit and quality reports
- `data/stream`: streaming events, alerts, and logs

## Docker

```powershell
docker compose up loan-intelligence
```

Optional services for Kafka and Airflow are declared in `docker-compose.yml`. Airflow DAGs live in `dags/`.

## BigQuery and dbt

Use `sql/bigquery/ddl.sql` to create warehouse tables and `sql/bigquery/kpi_views.sql` for dashboard views. The dbt scaffold in `dbt/` mirrors the bronze, silver, and gold model layout for a BigQuery deployment.

## Documentation

- `docs/architecture.md`
- `docs/setup_guide.md`
- `docs/etl_documentation.md`
- `docs/data_dictionary.md`
- `docs/data_quality.md`
- `architecture/er_diagram.mmd`
- `architecture/data_flow.mmd`
