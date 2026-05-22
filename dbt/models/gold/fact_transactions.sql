SELECT
  t.transaction_id,
  c.customer_key,
  CAST(FORMAT_DATE('%Y%m%d', t.transaction_date) AS INT64) AS transaction_date_key,
  t.transaction_type,
  t.amount,
  t.channel,
  t.merchant_category
FROM {{ ref('silver_mobile_transactions') }} t
JOIN {{ ref('dim_customer') }} c USING (customer_id)
