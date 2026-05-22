SELECT
  UPPER(TRIM(collection_id)) AS collection_id,
  UPPER(TRIM(loan_id)) AS loan_id,
  UPPER(TRIM(customer_id)) AS customer_id,
  UPPER(TRIM(collector_id)) AS collector_id,
  SAFE_CAST(action_date AS DATE) AS action_date,
  LOWER(TRIM(action_type)) AS action_type,
  SAFE_CAST(amount_recovered AS NUMERIC) AS amount_recovered,
  LOWER(TRIM(outcome)) AS outcome
FROM {{ source('raw', 'collections') }}
WHERE collection_id IS NOT NULL
  AND SAFE_CAST(amount_recovered AS NUMERIC) >= 0
QUALIFY ROW_NUMBER() OVER (PARTITION BY collection_id ORDER BY action_date DESC) = 1
