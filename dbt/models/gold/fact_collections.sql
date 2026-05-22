SELECT
  col.collection_id,
  col.loan_id,
  c.customer_key,
  CAST(FORMAT_DATE('%Y%m%d', col.action_date) AS INT64) AS action_date_key,
  col.collector_id,
  col.action_type,
  col.amount_recovered,
  col.outcome
FROM {{ ref('silver_collections') }} col
JOIN {{ ref('dim_customer') }} c USING (customer_id)
