-- BigQuery warehouse DDL for the Loan & Customer Intelligence Platform.
-- Replace `loan_intelligence` with your target dataset name as needed.

CREATE SCHEMA IF NOT EXISTS `loan_intelligence`
OPTIONS(location = "US");

CREATE TABLE IF NOT EXISTS `loan_intelligence.dim_customer` (
  customer_key INT64 NOT NULL,
  customer_id STRING NOT NULL,
  full_name STRING,
  gender STRING,
  branch_id STRING,
  signup_date DATE,
  monthly_income NUMERIC,
  customer_segment STRING,
  loan_utilization_band STRING,
  effective_from DATE,
  effective_to DATE,
  is_current BOOL
);

CREATE TABLE IF NOT EXISTS `loan_intelligence.dim_product` (
  product_key INT64 NOT NULL,
  product_id STRING NOT NULL,
  product_name STRING,
  product_type STRING,
  base_rate NUMERIC
);

CREATE TABLE IF NOT EXISTS `loan_intelligence.dim_branch` (
  branch_key INT64 NOT NULL,
  branch_id STRING NOT NULL,
  branch_name STRING,
  region STRING
);

CREATE TABLE IF NOT EXISTS `loan_intelligence.dim_date` (
  date_key INT64 NOT NULL,
  full_date DATE NOT NULL,
  year INT64,
  quarter INT64,
  month INT64,
  day INT64,
  day_name STRING
);

CREATE TABLE IF NOT EXISTS `loan_intelligence.dim_loan_status` (
  loan_status_key INT64 NOT NULL,
  loan_status STRING NOT NULL
);

CREATE TABLE IF NOT EXISTS `loan_intelligence.fact_loan_disbursement` (
  loan_id STRING NOT NULL,
  customer_key INT64 NOT NULL,
  product_key INT64 NOT NULL,
  branch_key INT64 NOT NULL,
  loan_status_key INT64 NOT NULL,
  disbursement_date_key INT64 NOT NULL,
  loan_amount NUMERIC,
  amount_repaid NUMERIC,
  amount_recovered NUMERIC,
  outstanding_amount NUMERIC,
  term_months INT64,
  interest_rate NUMERIC
)
PARTITION BY RANGE_BUCKET(disbursement_date_key, GENERATE_ARRAY(20200101, 20301231, 10000))
CLUSTER BY branch_key, product_key, loan_status_key;

CREATE TABLE IF NOT EXISTS `loan_intelligence.fact_repayments` (
  repayment_id STRING NOT NULL,
  loan_id STRING NOT NULL,
  customer_key INT64 NOT NULL,
  repayment_date_key INT64 NOT NULL,
  amount_paid NUMERIC,
  payment_channel STRING
)
PARTITION BY RANGE_BUCKET(repayment_date_key, GENERATE_ARRAY(20200101, 20301231, 10000))
CLUSTER BY customer_key, payment_channel;

CREATE TABLE IF NOT EXISTS `loan_intelligence.fact_collections` (
  collection_id STRING NOT NULL,
  loan_id STRING NOT NULL,
  customer_key INT64 NOT NULL,
  action_date_key INT64 NOT NULL,
  collector_id STRING,
  action_type STRING,
  amount_recovered NUMERIC,
  outcome STRING
)
PARTITION BY RANGE_BUCKET(action_date_key, GENERATE_ARRAY(20200101, 20301231, 10000))
CLUSTER BY collector_id, outcome;

CREATE TABLE IF NOT EXISTS `loan_intelligence.fact_transactions` (
  transaction_id STRING NOT NULL,
  customer_key INT64 NOT NULL,
  transaction_date_key INT64 NOT NULL,
  transaction_type STRING,
  amount NUMERIC,
  channel STRING,
  merchant_category STRING
)
PARTITION BY RANGE_BUCKET(transaction_date_key, GENERATE_ARRAY(20200101, 20301231, 10000))
CLUSTER BY customer_key, transaction_type;

CREATE TABLE IF NOT EXISTS `loan_intelligence.portfolio_summary` (
  metric STRING NOT NULL,
  value STRING
);
