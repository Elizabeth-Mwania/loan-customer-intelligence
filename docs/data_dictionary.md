# Data Dictionary

## Dimensions

### dim_customer

| Column | Description |
| --- | --- |
| customer_key | Surrogate customer key |
| customer_id | Source customer identifier |
| full_name | Customer display name |
| gender | Customer gender |
| branch_id | Home branch identifier |
| signup_date | Customer onboarding date |
| monthly_income | Declared monthly income |
| customer_segment | Segment derived from income and default history |
| loan_utilization_band | Utilization band derived from total disbursed loans |
| effective_from | SCD effective start date |
| effective_to | SCD effective end date |
| is_current | Current SCD record flag |

### dim_product

| Column | Description |
| --- | --- |
| product_key | Surrogate product key |
| product_id | Source product identifier |
| product_name | Product name |
| product_type | Product category |
| base_rate | Base interest rate |

### dim_branch

| Column | Description |
| --- | --- |
| branch_key | Surrogate branch key |
| branch_id | Source branch identifier |
| branch_name | Branch name |
| region | Operating region |

### dim_date

| Column | Description |
| --- | --- |
| date_key | Date in YYYYMMDD format |
| full_date | Calendar date |
| year | Calendar year |
| quarter | Calendar quarter |
| month | Calendar month |
| day | Day of month |
| day_name | Weekday name |

## Facts

### fact_loan_disbursement

| Column | Description |
| --- | --- |
| loan_id | Source loan identifier |
| customer_key | Customer dimension key |
| product_key | Product dimension key |
| branch_key | Branch dimension key |
| loan_status_key | Loan status dimension key |
| disbursement_date_key | Date key for disbursement |
| loan_amount | Original disbursed principal |
| amount_repaid | Total repayments received |
| amount_recovered | Total collection recoveries |
| outstanding_amount | Remaining principal estimate |
| term_months | Loan term |
| interest_rate | Interest rate |

### fact_repayments

Repayment events by loan, customer, date, amount, and payment channel.

### fact_collections

Collections activity by collector, action type, outcome, recovered amount, and date.

### fact_transactions

Mobile money transaction events by customer, date, transaction type, amount, channel, and merchant category.
