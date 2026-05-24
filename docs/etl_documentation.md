# ETL Documentation

## Batch Workflow

The batch pipeline is implemented by `LoanIntelligencePipeline` in `src/loan_intelligence/etl.py`.

### Steps

1. Generate source extracts when source files are missing.
2. Load each source CSV to bronze and add `_ingested_at` plus `_source_file`.
3. Clean and validate source-specific records into silver.
4. Write invalid records to quarantine files.
5. Build gold dimensions, fact tables, and `portfolio_summary`.
6. Write an audit JSON file with row counts and quality issues.

## Incremental Loading

The local scaffold is file based and deterministic. For a warehouse deployment, use the source primary keys and date fields as incremental keys:

| Table | Primary key | Incremental field |
| --- | --- | --- |
| customers | customer_id | signup_date |
| loans | loan_id | disbursement_date |
| repayments | repayment_id | repayment_date |
| mobile_transactions | transaction_id | transaction_date |
| collections | collection_id | action_date |
| fraud_alerts | alert_id | alert_timestamp |

## Retry and Logging

Airflow retries are configured in `dags/loan_intelligence_pipeline.py`. Local audit logs are written under `logs/etl_runs`.
