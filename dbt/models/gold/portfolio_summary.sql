WITH loan_metrics AS (
  SELECT
    SUM(loan_amount) AS total_disbursed,
    SUM(amount_repaid) AS total_repaid,
    SUM(amount_recovered) AS total_recovered,
    SUM(outstanding_amount) AS total_loan_book,
    SUM(CASE WHEN s.loan_status = 'OVERDUE' THEN outstanding_amount ELSE 0 END) AS overdue_principal,
    COUNTIF(s.loan_status = 'ACTIVE') AS active_loans,
    COUNTIF(s.loan_status = 'DEFAULTED') AS defaulted_loans
  FROM {{ ref('fact_loan_disbursement') }} f
  JOIN {{ ref('dim_loan_status') }} s USING (loan_status_key)
)
SELECT 'total_loan_book' AS metric, CAST(total_loan_book AS STRING) AS value FROM loan_metrics
UNION ALL
SELECT 'total_disbursed', CAST(total_disbursed AS STRING) FROM loan_metrics
UNION ALL
SELECT 'total_repaid', CAST(total_repaid AS STRING) FROM loan_metrics
UNION ALL
SELECT 'total_recovered', CAST(total_recovered AS STRING) FROM loan_metrics
UNION ALL
SELECT 'overdue_principal', CAST(overdue_principal AS STRING) FROM loan_metrics
UNION ALL
SELECT 'repayment_rate_pct', CAST(SAFE_DIVIDE(total_repaid, total_disbursed) * 100 AS STRING) FROM loan_metrics
UNION ALL
SELECT 'recovery_rate_pct', CAST(SAFE_DIVIDE(total_recovered, total_recovered + total_loan_book) * 100 AS STRING) FROM loan_metrics
UNION ALL
SELECT 'active_loans', CAST(active_loans AS STRING) FROM loan_metrics
UNION ALL
SELECT 'defaulted_loans', CAST(defaulted_loans AS STRING) FROM loan_metrics
