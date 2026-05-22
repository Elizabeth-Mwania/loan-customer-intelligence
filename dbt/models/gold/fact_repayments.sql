SELECT
  r.repayment_id,
  r.loan_id,
  c.customer_key,
  CAST(FORMAT_DATE('%Y%m%d', r.repayment_date) AS INT64) AS repayment_date_key,
  r.amount_paid,
  r.payment_channel
FROM {{ ref('silver_repayments') }} r
JOIN {{ ref('dim_customer') }} c USING (customer_id)
