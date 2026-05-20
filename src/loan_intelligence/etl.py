"""End-to-end local ETL pipeline for the Loan Intelligence platform."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .analytics import customer_segment, loan_utilization_band
from .config import SOURCE_TABLES, PlatformPaths, default_paths
from .generate_sources import generate_all
from .quality import (
    DataQualityReport,
    invalid_allowed_values,
    invalid_positive_decimal,
    missing_required,
    row_count_reconciles,
)
from .utils import clean_text, date_key, money, parse_decimal, read_csv, utc_now_iso, write_csv, write_json


@dataclass
class PipelineResult:
    run_id: str
    status: str
    audit_log: Path
    report: DataQualityReport


class LoanIntelligencePipeline:
    """Pipeline that moves source data through bronze, silver, and gold layers."""

    def __init__(self, paths: PlatformPaths | None = None) -> None:
        self.paths = paths or default_paths()

    def run(self, generate_if_missing: bool = True) -> PipelineResult:
        self.paths.ensure()
        if generate_if_missing and not (self.paths.source / "customers.csv").exists():
            generate_all(self.paths)

        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report = DataQualityReport(run_id=run_id)

        self.load_bronze(report)
        self.build_silver(report)
        self.build_gold(report)

        audit = {
            "run_id": run_id,
            "status": report.status,
            "started_at": run_id,
            "completed_at": utc_now_iso(),
            "layers": {
                "bronze": str(self.paths.bronze),
                "silver": str(self.paths.silver),
                "gold": str(self.paths.gold),
                "quarantine": str(self.paths.quarantine),
            },
            "quality": report.to_dict(),
        }
        audit_log = self.paths.etl_logs / f"{run_id}.json"
        write_json(audit_log, audit)
        return PipelineResult(run_id=run_id, status=report.status, audit_log=audit_log, report=report)

    def load_bronze(self, report: DataQualityReport) -> None:
        ingested_at = utc_now_iso()
        for table in SOURCE_TABLES:
            source_file = self.paths.source / f"{table}.csv"
            bronze_file = self.paths.bronze / f"{table}.csv"
            if not source_file.exists():
                report.add_issue(table, "source_file_exists", "error", f"Missing source file: {source_file}", 1)
                continue
            rows = read_csv(source_file)
            enriched = []
            for row in rows:
                enriched_row = dict(row)
                enriched_row["_ingested_at"] = ingested_at
                enriched_row["_source_file"] = source_file.name
                enriched.append(enriched_row)
            write_csv(bronze_file, enriched)
            report.row_counts[f"bronze.{table}"] = len(enriched)

    def build_silver(self, report: DataQualityReport) -> None:
        valid_customers = self._clean_customers(report)
        valid_products = self._copy_reference("products", "product_id", report)
        valid_branches = self._copy_reference("branches", "branch_id", report)
        valid_loans = self._clean_loans(valid_customers, valid_products, valid_branches, report)
        self._clean_repayments(valid_loans, valid_customers, report)
        self._clean_transactions(valid_customers, report)
        self._clean_collections(valid_loans, valid_customers, report)
        self._clean_fraud_alerts(valid_customers, report)

    def build_gold(self, report: DataQualityReport) -> None:
        customers = read_csv(self.paths.silver / "customers.csv")
        products = read_csv(self.paths.silver / "products.csv")
        branches = read_csv(self.paths.silver / "branches.csv")
        loans = read_csv(self.paths.silver / "loans.csv")
        repayments = read_csv(self.paths.silver / "repayments.csv")
        transactions = read_csv(self.paths.silver / "mobile_transactions.csv")
        collections = read_csv(self.paths.silver / "collections.csv")

        repayment_by_loan = self._sum_by(repayments, "loan_id", "amount_paid")
        collection_by_loan = self._sum_by(collections, "loan_id", "amount_recovered")
        loans_by_customer: dict[str, list[dict[str, str]]] = {}
        for loan in loans:
            loans_by_customer.setdefault(loan["customer_id"], []).append(loan)

        dim_customer = []
        customer_key_by_id: dict[str, int] = {}
        for key, customer in enumerate(sorted(customers, key=lambda item: item["customer_id"]), start=1):
            customer_loans = loans_by_customer.get(customer["customer_id"], [])
            defaulted = sum(1 for loan in customer_loans if loan["loan_status"] == "DEFAULTED")
            total_disbursed = sum((parse_decimal(loan["loan_amount"]) for loan in customer_loans), Decimal("0"))
            customer_key_by_id[customer["customer_id"]] = key
            dim_customer.append(
                {
                    "customer_key": key,
                    "customer_id": customer["customer_id"],
                    "full_name": f"{customer['first_name']} {customer['last_name']}",
                    "gender": customer["gender"],
                    "branch_id": customer["branch_id"],
                    "signup_date": customer["signup_date"],
                    "monthly_income": customer["monthly_income"],
                    "customer_segment": customer_segment(customer["monthly_income"], defaulted),
                    "loan_utilization_band": loan_utilization_band(total_disbursed),
                    "effective_from": customer["signup_date"],
                    "effective_to": "",
                    "is_current": "true",
                }
            )

        dim_product = [
            {
                "product_key": idx,
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "product_type": row["product_type"],
                "base_rate": row["base_rate"],
            }
            for idx, row in enumerate(sorted(products, key=lambda item: item["product_id"]), start=1)
        ]
        product_key_by_id = {row["product_id"]: row["product_key"] for row in dim_product}

        dim_branch = [
            {
                "branch_key": idx,
                "branch_id": row["branch_id"],
                "branch_name": row["branch_name"],
                "region": row["region"],
            }
            for idx, row in enumerate(sorted(branches, key=lambda item: item["branch_id"]), start=1)
        ]
        branch_key_by_id = {row["branch_id"]: row["branch_key"] for row in dim_branch}

        statuses = sorted({loan["loan_status"] for loan in loans} | {"ACTIVE", "CLOSED", "OVERDUE", "DEFAULTED"})
        dim_loan_status = [{"loan_status_key": idx, "loan_status": status} for idx, status in enumerate(statuses, start=1)]
        loan_status_key_by_status = {row["loan_status"]: row["loan_status_key"] for row in dim_loan_status}

        fact_loan_disbursement = []
        fact_repayments = []
        fact_collections = []
        fact_transactions = []
        dates: set[str] = set()

        for loan in loans:
            dates.add(loan["disbursement_date"])
            principal = parse_decimal(loan["loan_amount"])
            paid = repayment_by_loan.get(loan["loan_id"], Decimal("0"))
            recovered = collection_by_loan.get(loan["loan_id"], Decimal("0"))
            outstanding = max(principal - paid - recovered, Decimal("0"))
            fact_loan_disbursement.append(
                {
                    "loan_id": loan["loan_id"],
                    "customer_key": customer_key_by_id[loan["customer_id"]],
                    "product_key": product_key_by_id[loan["product_id"]],
                    "branch_key": branch_key_by_id[loan["branch_id"]],
                    "loan_status_key": loan_status_key_by_status[loan["loan_status"]],
                    "disbursement_date_key": date_key(loan["disbursement_date"]),
                    "loan_amount": money(principal),
                    "amount_repaid": money(paid),
                    "amount_recovered": money(recovered),
                    "outstanding_amount": money(outstanding),
                    "term_months": loan["term_months"],
                    "interest_rate": loan["interest_rate"],
                }
            )

        for repayment in repayments:
            dates.add(repayment["repayment_date"])
            fact_repayments.append(
                {
                    "repayment_id": repayment["repayment_id"],
                    "loan_id": repayment["loan_id"],
                    "customer_key": customer_key_by_id[repayment["customer_id"]],
                    "repayment_date_key": date_key(repayment["repayment_date"]),
                    "amount_paid": repayment["amount_paid"],
                    "payment_channel": repayment["payment_channel"],
                }
            )

        for collection in collections:
            dates.add(collection["action_date"])
            fact_collections.append(
                {
                    "collection_id": collection["collection_id"],
                    "loan_id": collection["loan_id"],
                    "customer_key": customer_key_by_id[collection["customer_id"]],
                    "action_date_key": date_key(collection["action_date"]),
                    "collector_id": collection["collector_id"],
                    "action_type": collection["action_type"],
                    "amount_recovered": collection["amount_recovered"],
                    "outcome": collection["outcome"],
                }
            )

        for transaction in transactions:
            dates.add(transaction["transaction_date"])
            fact_transactions.append(
                {
                    "transaction_id": transaction["transaction_id"],
                    "customer_key": customer_key_by_id[transaction["customer_id"]],
                    "transaction_date_key": date_key(transaction["transaction_date"]),
                    "transaction_type": transaction["transaction_type"],
                    "amount": transaction["amount"],
                    "channel": transaction["channel"],
                    "merchant_category": transaction["merchant_category"],
                }
            )

        dim_date = []
        for raw_date in sorted(date for date in dates if date):
            dt = datetime.strptime(raw_date, "%Y-%m-%d").date()
            dim_date.append(
                {
                    "date_key": date_key(raw_date),
                    "full_date": raw_date,
                    "year": dt.year,
                    "quarter": (dt.month - 1) // 3 + 1,
                    "month": dt.month,
                    "day": dt.day,
                    "day_name": dt.strftime("%A"),
                }
            )

        total_disbursed = sum((parse_decimal(row["loan_amount"]) for row in fact_loan_disbursement), Decimal("0"))
        total_repaid = sum((parse_decimal(row["amount_paid"]) for row in fact_repayments), Decimal("0"))
        total_recovered = sum((parse_decimal(row["amount_recovered"]) for row in fact_collections), Decimal("0"))
        outstanding = sum((parse_decimal(row["outstanding_amount"]) for row in fact_loan_disbursement), Decimal("0"))
        overdue = sum(
            (
                parse_decimal(row["outstanding_amount"])
                for row in fact_loan_disbursement
                if row["loan_status_key"] == loan_status_key_by_status.get("OVERDUE")
            ),
            Decimal("0"),
        )
        repayment_rate = Decimal("0") if total_disbursed == 0 else (total_repaid / total_disbursed) * Decimal("100")
        recovery_rate = Decimal("0") if outstanding == 0 else (total_recovered / (total_recovered + outstanding)) * Decimal("100")
        portfolio_summary = [
            {"metric": "total_loan_book", "value": money(outstanding)},
            {"metric": "total_disbursed", "value": money(total_disbursed)},
            {"metric": "total_repaid", "value": money(total_repaid)},
            {"metric": "total_recovered", "value": money(total_recovered)},
            {"metric": "overdue_principal", "value": money(overdue)},
            {"metric": "repayment_rate_pct", "value": money(repayment_rate)},
            {"metric": "recovery_rate_pct", "value": money(recovery_rate)},
            {"metric": "active_loans", "value": str(sum(1 for loan in loans if loan["loan_status"] == "ACTIVE"))},
            {"metric": "defaulted_loans", "value": str(sum(1 for loan in loans if loan["loan_status"] == "DEFAULTED"))},
        ]

        self._write_gold("dim_customer", dim_customer, report)
        self._write_gold("dim_product", dim_product, report)
        self._write_gold("dim_branch", dim_branch, report)
        self._write_gold("dim_date", dim_date, report)
        self._write_gold("dim_loan_status", dim_loan_status, report)
        self._write_gold("fact_loan_disbursement", fact_loan_disbursement, report)
        self._write_gold("fact_repayments", fact_repayments, report)
        self._write_gold("fact_collections", fact_collections, report)
        self._write_gold("fact_transactions", fact_transactions, report)
        self._write_gold("portfolio_summary", portfolio_summary, report)

    def _clean_customers(self, report: DataQualityReport) -> set[str]:
        rows = read_csv(self.paths.bronze / "customers.csv")
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in rows:
            errors = missing_required(row, ["customer_id", "first_name", "last_name", "branch_id", "signup_date"])
            errors.extend(invalid_positive_decimal(row, ["monthly_income"]))
            customer_id = clean_text(row.get("customer_id")).upper()
            if customer_id in seen:
                errors.append("duplicate_customer_id")
            if errors:
                rejected.append(self._reject(row, errors))
                continue
            seen.add(customer_id)
            accepted.append(
                {
                    "customer_id": customer_id,
                    "first_name": clean_text(row.get("first_name")).title(),
                    "last_name": clean_text(row.get("last_name")).title(),
                    "gender": clean_text(row.get("gender")).upper(),
                    "date_of_birth": clean_text(row.get("date_of_birth")),
                    "phone_number": clean_text(row.get("phone_number")),
                    "email": clean_text(row.get("email")).lower(),
                    "national_id": clean_text(row.get("national_id")),
                    "branch_id": clean_text(row.get("branch_id")).upper(),
                    "signup_date": clean_text(row.get("signup_date")),
                    "monthly_income": money(row.get("monthly_income")),
                    "employment_status": clean_text(row.get("employment_status")).lower(),
                }
            )
        return self._finish_clean("customers", rows, accepted, rejected, "customer_id", report)

    def _copy_reference(self, table: str, key: str, report: DataQualityReport) -> set[str]:
        rows = read_csv(self.paths.bronze / f"{table}.csv")
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in rows:
            key_value = clean_text(row.get(key)).upper()
            errors = missing_required(row, [key])
            if key_value in seen:
                errors.append(f"duplicate_{key}")
            if errors:
                rejected.append(self._reject(row, errors))
                continue
            seen.add(key_value)
            clean_row = {field: clean_text(value) for field, value in row.items() if not field.startswith("_")}
            clean_row[key] = key_value
            accepted.append(clean_row)
        return self._finish_clean(table, rows, accepted, rejected, key, report)

    def _clean_loans(
        self,
        valid_customers: set[str],
        valid_products: set[str],
        valid_branches: set[str],
        report: DataQualityReport,
    ) -> set[str]:
        rows = read_csv(self.paths.bronze / "loans.csv")
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen: set[str] = set()
        allowed_status = {"ACTIVE", "CLOSED", "OVERDUE", "DEFAULTED"}
        for row in rows:
            loan_id = clean_text(row.get("loan_id")).upper()
            customer_id = clean_text(row.get("customer_id")).upper()
            product_id = clean_text(row.get("product_id")).upper()
            branch_id = clean_text(row.get("branch_id")).upper()
            status = clean_text(row.get("loan_status")).upper()
            errors = missing_required(row, ["loan_id", "customer_id", "product_id", "branch_id", "disbursement_date"])
            errors.extend(invalid_positive_decimal(row, ["loan_amount", "interest_rate", "term_months"]))
            errors.extend(invalid_allowed_values({"loan_status": status}, {"loan_status": allowed_status}))
            if loan_id in seen:
                errors.append("duplicate_loan_id")
            if customer_id not in valid_customers:
                errors.append("unknown_customer_id")
            if product_id not in valid_products:
                errors.append("unknown_product_id")
            if branch_id not in valid_branches:
                errors.append("unknown_branch_id")
            if errors:
                rejected.append(self._reject(row, errors))
                continue
            seen.add(loan_id)
            accepted.append(
                {
                    "loan_id": loan_id,
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "branch_id": branch_id,
                    "application_date": clean_text(row.get("application_date")),
                    "disbursement_date": clean_text(row.get("disbursement_date")),
                    "loan_amount": money(row.get("loan_amount")),
                    "interest_rate": money(row.get("interest_rate")),
                    "term_months": str(int(parse_decimal(row.get("term_months")))),
                    "loan_status": status,
                    "due_date": clean_text(row.get("due_date")),
                }
            )
        return self._finish_clean("loans", rows, accepted, rejected, "loan_id", report)

    def _clean_repayments(self, valid_loans: set[str], valid_customers: set[str], report: DataQualityReport) -> set[str]:
        rows = read_csv(self.paths.bronze / "repayments.csv")
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in rows:
            repayment_id = clean_text(row.get("repayment_id")).upper()
            loan_id = clean_text(row.get("loan_id")).upper()
            customer_id = clean_text(row.get("customer_id")).upper()
            errors = missing_required(row, ["repayment_id", "loan_id", "customer_id", "repayment_date"])
            errors.extend(invalid_positive_decimal(row, ["amount_paid"]))
            if repayment_id in seen:
                errors.append("duplicate_repayment_id")
            if loan_id not in valid_loans:
                errors.append("unknown_loan_id")
            if customer_id not in valid_customers:
                errors.append("unknown_customer_id")
            if errors:
                rejected.append(self._reject(row, errors))
                continue
            seen.add(repayment_id)
            accepted.append(
                {
                    "repayment_id": repayment_id,
                    "loan_id": loan_id,
                    "customer_id": customer_id,
                    "repayment_date": clean_text(row.get("repayment_date")),
                    "amount_paid": money(row.get("amount_paid")),
                    "payment_channel": clean_text(row.get("payment_channel")).lower(),
                }
            )
        return self._finish_clean("repayments", rows, accepted, rejected, "repayment_id", report)

    def _clean_transactions(self, valid_customers: set[str], report: DataQualityReport) -> set[str]:
        rows = read_csv(self.paths.bronze / "mobile_transactions.csv")
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in rows:
            transaction_id = clean_text(row.get("transaction_id")).upper()
            customer_id = clean_text(row.get("customer_id")).upper()
            errors = missing_required(row, ["transaction_id", "customer_id", "transaction_date", "transaction_type"])
            errors.extend(invalid_positive_decimal(row, ["amount"]))
            if transaction_id in seen:
                errors.append("duplicate_transaction_id")
            if customer_id not in valid_customers:
                errors.append("unknown_customer_id")
            if errors:
                rejected.append(self._reject(row, errors))
                continue
            seen.add(transaction_id)
            accepted.append(
                {
                    "transaction_id": transaction_id,
                    "customer_id": customer_id,
                    "transaction_date": clean_text(row.get("transaction_date")),
                    "transaction_type": clean_text(row.get("transaction_type")).lower(),
                    "amount": money(row.get("amount")),
                    "channel": clean_text(row.get("channel")).lower(),
                    "merchant_category": clean_text(row.get("merchant_category")).lower(),
                }
            )
        return self._finish_clean("mobile_transactions", rows, accepted, rejected, "transaction_id", report)

    def _clean_collections(self, valid_loans: set[str], valid_customers: set[str], report: DataQualityReport) -> set[str]:
        rows = read_csv(self.paths.bronze / "collections.csv")
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in rows:
            collection_id = clean_text(row.get("collection_id")).upper()
            loan_id = clean_text(row.get("loan_id")).upper()
            customer_id = clean_text(row.get("customer_id")).upper()
            errors = missing_required(row, ["collection_id", "loan_id", "customer_id", "collector_id", "action_date"])
            if parse_decimal(row.get("amount_recovered")) < Decimal("0"):
                errors.append("negative_amount_recovered")
            if collection_id in seen:
                errors.append("duplicate_collection_id")
            if loan_id not in valid_loans:
                errors.append("unknown_loan_id")
            if customer_id not in valid_customers:
                errors.append("unknown_customer_id")
            if errors:
                rejected.append(self._reject(row, errors))
                continue
            seen.add(collection_id)
            accepted.append(
                {
                    "collection_id": collection_id,
                    "loan_id": loan_id,
                    "customer_id": customer_id,
                    "collector_id": clean_text(row.get("collector_id")).upper(),
                    "action_date": clean_text(row.get("action_date")),
                    "action_type": clean_text(row.get("action_type")).lower(),
                    "amount_recovered": money(row.get("amount_recovered")),
                    "outcome": clean_text(row.get("outcome")).lower(),
                }
            )
        return self._finish_clean("collections", rows, accepted, rejected, "collection_id", report)

    def _clean_fraud_alerts(self, valid_customers: set[str], report: DataQualityReport) -> set[str]:
        rows = read_csv(self.paths.bronze / "fraud_alerts.csv")
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in rows:
            alert_id = clean_text(row.get("alert_id")).upper()
            customer_id = clean_text(row.get("customer_id")).upper()
            errors = missing_required(row, ["alert_id", "transaction_id", "customer_id", "alert_timestamp", "rule_name"])
            if parse_decimal(row.get("risk_score")) <= Decimal("0"):
                errors.append("invalid_risk_score")
            if alert_id in seen:
                errors.append("duplicate_alert_id")
            if customer_id not in valid_customers:
                errors.append("unknown_customer_id")
            if errors:
                rejected.append(self._reject(row, errors))
                continue
            seen.add(alert_id)
            accepted.append(
                {
                    "alert_id": alert_id,
                    "transaction_id": clean_text(row.get("transaction_id")).upper(),
                    "customer_id": customer_id,
                    "alert_timestamp": clean_text(row.get("alert_timestamp")),
                    "rule_name": clean_text(row.get("rule_name")).lower(),
                    "risk_score": str(int(parse_decimal(row.get("risk_score")))),
                    "alert_status": clean_text(row.get("alert_status")).upper(),
                }
            )
        return self._finish_clean("fraud_alerts", rows, accepted, rejected, "alert_id", report)

    def _finish_clean(
        self,
        table: str,
        source_rows: list[dict[str, str]],
        accepted: list[dict[str, str]],
        rejected: list[dict[str, str]],
        key: str,
        report: DataQualityReport,
    ) -> set[str]:
        write_csv(self.paths.silver / f"{table}.csv", accepted)
        write_csv(self.paths.quarantine / f"{table}_errors.csv", rejected)
        report.row_counts[f"silver.{table}"] = len(accepted)
        report.row_counts[f"quarantine.{table}"] = len(rejected)
        report.add_issue(
            table,
            "records_quarantined",
            "warning",
            f"{len(rejected)} rejected records written to quarantine",
            len(rejected),
        )
        if not row_count_reconciles(len(source_rows), len(accepted), len(rejected)):
            report.add_issue(table, "row_count_reconciliation", "error", "Accepted plus rejected rows does not equal source rows", 1)
        return {clean_text(row.get(key)).upper() for row in accepted}

    def _write_gold(self, table: str, rows: list[dict[str, object]], report: DataQualityReport) -> None:
        write_csv(self.paths.gold / f"{table}.csv", rows)
        report.row_counts[f"gold.{table}"] = len(rows)

    @staticmethod
    def _reject(row: dict[str, str], errors: list[str]) -> dict[str, str]:
        rejected = {field: value for field, value in row.items() if not field.startswith("_")}
        rejected["error_reason"] = "|".join(errors)
        return rejected

    @staticmethod
    def _sum_by(rows: list[dict[str, str]], key: str, amount_field: str) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}
        for row in rows:
            totals[row[key]] = totals.get(row[key], Decimal("0")) + parse_decimal(row[amount_field])
        return totals

    def reset_outputs(self) -> None:
        """Remove generated layer outputs while leaving source data intact."""

        for path in [self.paths.bronze, self.paths.silver, self.paths.gold, self.paths.quarantine, self.paths.stream]:
            if path.exists():
                shutil.rmtree(path)
        self.paths.ensure()
