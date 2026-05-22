SELECT
  l.loan_id,
  c.customer_key,
  p.product_key,
  b.branch_key,
  s.loan_status_key,
  CAST(FORMAT_DATE('%Y%m%d', l.disbursement_date) AS INT64) AS disbursement_date_key,
  l.loan_amount,
  COALESCE(r.amount_repaid, 0) AS amount_repaid,
  COALESCE(col.amount_recovered, 0) AS amount_recovered,
  GREATEST(l.loan_amount - COALESCE(r.amount_repaid, 0) - COALESCE(col.amount_recovered, 0), 0) AS outstanding_amount,
  l.term_months,
  l.interest_rate
FROM {{ ref('silver_loans') }} l
JOIN {{ ref('dim_customer') }} c USING (customer_id)
JOIN {{ ref('dim_product') }} p USING (product_id)
JOIN {{ ref('dim_branch') }} b USING (branch_id)
JOIN {{ ref('dim_loan_status') }} s USING (loan_status)
LEFT JOIN (
  SELECT loan_id, SUM(amount_paid) AS amount_repaid
  FROM {{ ref('silver_repayments') }}
  GROUP BY loan_id
) r USING (loan_id)
LEFT JOIN (
  SELECT loan_id, SUM(amount_recovered) AS amount_recovered
  FROM {{ ref('silver_collections') }}
  GROUP BY loan_id
) col USING (loan_id)
