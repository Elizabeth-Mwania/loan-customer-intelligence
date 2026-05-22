SELECT
  ROW_NUMBER() OVER (ORDER BY branch_id) AS branch_key,
  UPPER(TRIM(branch_id)) AS branch_id,
  TRIM(branch_name) AS branch_name,
  TRIM(region) AS region
FROM {{ source('raw', 'branches') }}
