SELECT
  UPPER(TRIM(customer_id)) AS customer_id,
  INITCAP(TRIM(first_name)) AS first_name,
  INITCAP(TRIM(last_name)) AS last_name,
  UPPER(TRIM(gender)) AS gender,
  SAFE_CAST(date_of_birth AS DATE) AS date_of_birth,
  TRIM(phone_number) AS phone_number,
  LOWER(TRIM(email)) AS email,
  TRIM(national_id) AS national_id,
  UPPER(TRIM(branch_id)) AS branch_id,
  SAFE_CAST(signup_date AS DATE) AS signup_date,
  SAFE_CAST(monthly_income AS NUMERIC) AS monthly_income,
  LOWER(TRIM(employment_status)) AS employment_status
FROM {{ source('raw', 'customers') }}
WHERE customer_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY signup_date DESC) = 1
