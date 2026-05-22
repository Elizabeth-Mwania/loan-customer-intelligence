SELECT
  UPPER(TRIM(transaction_id)) AS transaction_id,
  UPPER(TRIM(customer_id)) AS customer_id,
  SAFE_CAST(transaction_date AS DATE) AS transaction_date,
  LOWER(TRIM(transaction_type)) AS transaction_type,
  SAFE_CAST(amount AS NUMERIC) AS amount,
  LOWER(TRIM(channel)) AS channel,
  LOWER(TRIM(merchant_category)) AS merchant_category
FROM {{ source('raw', 'mobile_transactions') }}
WHERE transaction_id IS NOT NULL
  AND SAFE_CAST(amount AS NUMERIC) > 0
QUALIFY ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY transaction_date DESC) = 1
