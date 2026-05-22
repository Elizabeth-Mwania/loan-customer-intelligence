SELECT
  ROW_NUMBER() OVER (ORDER BY loan_status) AS loan_status_key,
  loan_status
FROM (
  SELECT DISTINCT loan_status
  FROM {{ ref('silver_loans') }}
)
