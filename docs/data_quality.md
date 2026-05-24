# Data Quality

The platform validates data during silver-layer processing and writes rejected records to `data/quarantine`.

## Checks

| Check | Behavior |
| --- | --- |
| Required fields | Reject records with missing primary identifiers or dates |
| Duplicate keys | Keep the first valid record and quarantine duplicate keys |
| Numeric validation | Reject negative or zero loan, repayment, transaction, and risk values where inappropriate |
| Referential checks | Reject facts that reference unknown customers, loans, products, or branches |
| Row reconciliation | Verify source count equals accepted plus rejected records |
| Schema standardization | Normalize case, trim whitespace, and cast numeric values |

## Status Values

- `passed`: no quality issues.
- `passed_with_warnings`: records were quarantined but the pipeline completed.
- `failed`: a critical error such as missing source files or row-count mismatch occurred.
