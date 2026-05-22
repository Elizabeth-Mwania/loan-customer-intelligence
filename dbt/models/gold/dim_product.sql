SELECT
  ROW_NUMBER() OVER (ORDER BY product_id) AS product_key,
  UPPER(TRIM(product_id)) AS product_id,
  TRIM(product_name) AS product_name,
  TRIM(product_type) AS product_type,
  SAFE_CAST(base_rate AS NUMERIC) AS base_rate
FROM {{ source('raw', 'products') }}
