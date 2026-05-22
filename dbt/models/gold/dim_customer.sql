WITH loan_rollup AS (
  SELECT
    customer_id,
    COUNTIF(loan_status = 'DEFAULTED') AS defaulted_loans,
    SUM(loan_amount) AS total_disbursed
  FROM {{ ref('silver_loans') }}
  GROUP BY customer_id
)
SELECT
  ROW_NUMBER() OVER (ORDER BY c.customer_id) AS customer_key,
  c.customer_id,
  CONCAT(c.first_name, ' ', c.last_name) AS full_name,
  c.gender,
  c.branch_id,
  c.signup_date,
  c.monthly_income,
  CASE
    WHEN COALESCE(l.defaulted_loans, 0) > 0 THEN 'high_risk'
    WHEN c.monthly_income >= 150000 THEN 'premium'
    WHEN c.monthly_income >= 70000 THEN 'mass_affluent'
    ELSE 'emerging'
  END AS customer_segment,
  CASE
    WHEN COALESCE(l.total_disbursed, 0) >= 1000000 THEN 'high_utilization'
    WHEN COALESCE(l.total_disbursed, 0) >= 250000 THEN 'moderate_utilization'
    WHEN COALESCE(l.total_disbursed, 0) > 0 THEN 'low_utilization'
    ELSE 'no_loans'
  END AS loan_utilization_band,
  c.signup_date AS effective_from,
  CAST(NULL AS DATE) AS effective_to,
  TRUE AS is_current
FROM {{ ref('silver_customers') }} c
LEFT JOIN loan_rollup l USING (customer_id)
