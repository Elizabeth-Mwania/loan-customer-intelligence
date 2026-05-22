SELECT
  UPPER(TRIM(loan_id)) AS loan_id,
  UPPER(TRIM(customer_id)) AS customer_id,
  UPPER(TRIM(product_id)) AS product_id,
  UPPER(TRIM(branch_id)) AS branch_id,
  SAFE_CAST(application_date AS DATE) AS application_date,
  SAFE_CAST(disbursement_date AS DATE) AS disbursement_date,
  SAFE_CAST(loan_amount AS NUMERIC) AS loan_amount,
  SAFE_CAST(interest_rate AS NUMERIC) AS interest_rate,
  SAFE_CAST(term_months AS INT64) AS term_months,
  UPPER(TRIM(loan_status)) AS loan_status,
  SAFE_CAST(due_date AS DATE) AS due_date
FROM {{ source('raw', 'loans') }}
WHERE loan_id IS NOT NULL
  AND SAFE_CAST(loan_amount AS NUMERIC) > 0
QUALIFY ROW_NUMBER() OVER (PARTITION BY loan_id ORDER BY disbursement_date DESC) = 1
