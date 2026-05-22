SELECT
  UPPER(TRIM(repayment_id)) AS repayment_id,
  UPPER(TRIM(loan_id)) AS loan_id,
  UPPER(TRIM(customer_id)) AS customer_id,
  SAFE_CAST(repayment_date AS DATE) AS repayment_date,
  SAFE_CAST(amount_paid AS NUMERIC) AS amount_paid,
  LOWER(TRIM(payment_channel)) AS payment_channel
FROM {{ source('raw', 'repayments') }}
WHERE repayment_id IS NOT NULL
  AND SAFE_CAST(amount_paid AS NUMERIC) > 0
QUALIFY ROW_NUMBER() OVER (PARTITION BY repayment_id ORDER BY repayment_date DESC) = 1
