WITH dates AS (
  SELECT disbursement_date AS full_date FROM {{ ref('silver_loans') }}
  UNION DISTINCT
  SELECT repayment_date AS full_date FROM {{ ref('silver_repayments') }}
  UNION DISTINCT
  SELECT action_date AS full_date FROM {{ ref('silver_collections') }}
  UNION DISTINCT
  SELECT transaction_date AS full_date FROM {{ ref('silver_mobile_transactions') }}
)
SELECT
  CAST(FORMAT_DATE('%Y%m%d', full_date) AS INT64) AS date_key,
  full_date,
  EXTRACT(YEAR FROM full_date) AS year,
  EXTRACT(QUARTER FROM full_date) AS quarter,
  EXTRACT(MONTH FROM full_date) AS month,
  EXTRACT(DAY FROM full_date) AS day,
  FORMAT_DATE('%A', full_date) AS day_name
FROM dates
WHERE full_date IS NOT NULL
