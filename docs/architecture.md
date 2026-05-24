# Architecture

The platform follows a layered lakehouse-style warehouse pattern:

1. Source systems generate CSV extracts for customer, loan, repayment, mobile transaction, collection, and fraud monitoring domains.
2. Bronze stores raw records and ingestion metadata.
3. Silver standardizes identifiers, normalizes values, validates schemas, and quarantines invalid records.
4. Gold publishes star-schema facts and dimensions for BI and analytics.
5. Streaming simulation writes real-time transaction events and suspicious transaction alerts.
6. Airflow schedules pipeline execution and retries failed tasks.
7. dbt and BigQuery assets provide the target enterprise warehouse implementation path.

## Components

| Component | Local implementation | Enterprise target |
| --- | --- | --- |
| Source systems | Generated CSV files | Core banking, mobile money, collections, fraud systems |
| ETL | Python package in `src/loan_intelligence` | Python plus Airflow |
| Storage layers | CSV folders under `data/` | BigQuery datasets |
| Transformations | Python gold builder and dbt SQL | dbt on BigQuery |
| Streaming | JSONL producer and consumer | Kafka topics and consumers |
| BI | KPI view definitions and dashboard spec | Power BI |
| Quality | Python validation and quarantine files | dbt tests, warehouse checks, audit tables |

## Reliability

Each run writes an audit JSON file to `logs/etl_runs`. Failed records are isolated in `data/quarantine` with an `error_reason` field so valid records can continue through the pipeline.
