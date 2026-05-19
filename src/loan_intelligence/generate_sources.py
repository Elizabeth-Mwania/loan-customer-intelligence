"""Deterministic simulated source-system data generator."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from .config import PlatformPaths, default_paths
from .utils import money, write_csv


FIRST_NAMES = [
    "Amina",
    "Brian",
    "Caroline",
    "David",
    "Esther",
    "Felix",
    "Grace",
    "Hassan",
    "Ivy",
    "Joseph",
    "Lilian",
    "Moses",
    "Nadia",
    "Oscar",
    "Priscah",
    "Quincy",
]

LAST_NAMES = [
    "Otieno",
    "Wanjiku",
    "Mwangi",
    "Achieng",
    "Kiptoo",
    "Mutiso",
    "Njeri",
    "Omondi",
    "Cherono",
    "Kariuki",
]

BRANCHES = [
    {"branch_id": "BR001", "branch_name": "Nairobi CBD", "region": "Nairobi"},
    {"branch_id": "BR002", "branch_name": "Westlands", "region": "Nairobi"},
    {"branch_id": "BR003", "branch_name": "Mombasa", "region": "Coast"},
    {"branch_id": "BR004", "branch_name": "Kisumu", "region": "Western"},
    {"branch_id": "BR005", "branch_name": "Eldoret", "region": "Rift Valley"},
]

PRODUCTS = [
    {"product_id": "PRD001", "product_name": "Salary Advance", "product_type": "Consumer", "base_rate": "12.50"},
    {"product_id": "PRD002", "product_name": "SME Working Capital", "product_type": "SME", "base_rate": "16.00"},
    {"product_id": "PRD003", "product_name": "Asset Finance", "product_type": "Secured", "base_rate": "14.25"},
    {"product_id": "PRD004", "product_name": "Mobile Microloan", "product_type": "Digital", "base_rate": "18.00"},
]


def _iso(day: date) -> str:
    return day.isoformat()


def _pick(sequence: list[dict[str, str]]) -> dict[str, str]:
    return random.choice(sequence)


def generate_all(paths: PlatformPaths | None = None, customer_count: int = 120, seed: int = 42) -> None:
    """Create source CSV files with realistic referential relationships.

    A tiny number of dirty rows are deliberately included so quarantine and
    validation behavior can be demonstrated in a repeatable way.
    """

    paths = paths or default_paths()
    paths.ensure()
    random.seed(seed)

    today = date.today()
    start = today - timedelta(days=720)

    customers: list[dict[str, str]] = []
    for idx in range(1, customer_count + 1):
        branch = _pick(BRANCHES)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        signup = start + timedelta(days=random.randint(0, 650))
        income = Decimal(random.randint(28000, 220000))
        customer_id = f"CUST{idx:06d}"
        customers.append(
            {
                "customer_id": customer_id,
                "first_name": first,
                "last_name": last,
                "gender": random.choice(["F", "M"]),
                "date_of_birth": _iso(date(random.randint(1970, 2001), random.randint(1, 12), random.randint(1, 28))),
                "phone_number": f"+2547{random.randint(10000000, 99999999)}",
                "email": f"{first}.{last}{idx}@example.com".lower(),
                "national_id": f"{random.randint(10000000, 39999999)}",
                "branch_id": branch["branch_id"],
                "signup_date": _iso(signup),
                "monthly_income": money(income),
                "employment_status": random.choice(["salaried", "self_employed", "contract", "informal"]),
            }
        )

    dirty_duplicate = dict(customers[3])
    dirty_duplicate["email"] = "duplicate@example.com"
    customers.append(dirty_duplicate)
    dirty_missing = dict(customers[8])
    dirty_missing["customer_id"] = ""
    dirty_missing["email"] = "missing-id@example.com"
    customers.append(dirty_missing)

    loans: list[dict[str, str]] = []
    statuses = ["ACTIVE", "CLOSED", "OVERDUE", "DEFAULTED"]
    for idx in range(1, int(customer_count * 1.15) + 1):
        customer = random.choice(customers[:customer_count])
        branch = next(item for item in BRANCHES if item["branch_id"] == customer["branch_id"])
        product = _pick(PRODUCTS)
        application = start + timedelta(days=random.randint(30, 690))
        disbursement = application + timedelta(days=random.randint(1, 8))
        term = random.choice([1, 3, 6, 9, 12, 18, 24])
        principal = Decimal(random.randint(10000, 750000))
        status = random.choices(statuses, weights=[52, 28, 14, 6], k=1)[0]
        loans.append(
            {
                "loan_id": f"LN{idx:07d}",
                "customer_id": customer["customer_id"],
                "product_id": product["product_id"],
                "branch_id": branch["branch_id"],
                "application_date": _iso(application),
                "disbursement_date": _iso(disbursement),
                "loan_amount": money(principal),
                "interest_rate": product["base_rate"],
                "term_months": str(term),
                "loan_status": status,
                "due_date": _iso(disbursement + timedelta(days=30 * term)),
            }
        )

    loans.append(
        {
            "loan_id": "LN_BAD_AMOUNT",
            "customer_id": customers[0]["customer_id"],
            "product_id": PRODUCTS[0]["product_id"],
            "branch_id": BRANCHES[0]["branch_id"],
            "application_date": _iso(today),
            "disbursement_date": _iso(today),
            "loan_amount": "-2500.00",
            "interest_rate": "12.50",
            "term_months": "3",
            "loan_status": "ACTIVE",
            "due_date": _iso(today + timedelta(days=90)),
        }
    )

    repayments: list[dict[str, str]] = []
    collections: list[dict[str, str]] = []
    for idx, loan in enumerate(loans[:-1], start=1):
        amount = Decimal(loan["loan_amount"])
        paid_fraction = {
            "CLOSED": Decimal("1.00"),
            "ACTIVE": Decimal(random.choice(["0.10", "0.25", "0.40", "0.55"])),
            "OVERDUE": Decimal(random.choice(["0.00", "0.10", "0.18"])),
            "DEFAULTED": Decimal(random.choice(["0.00", "0.05", "0.12"])),
        }[loan["loan_status"]]
        paid_total = amount * paid_fraction
        if paid_total > 0:
            repayment_count = random.randint(1, min(5, max(1, int(Decimal(loan["term_months"]) / 3))))
            for pay_idx in range(1, repayment_count + 1):
                repayments.append(
                    {
                        "repayment_id": f"RP{idx:07d}{pay_idx:02d}",
                        "loan_id": loan["loan_id"],
                        "customer_id": loan["customer_id"],
                        "repayment_date": _iso(date.fromisoformat(loan["disbursement_date"]) + timedelta(days=30 * pay_idx)),
                        "amount_paid": money(paid_total / repayment_count),
                        "payment_channel": random.choice(["mpesa", "bank_transfer", "cash", "card"]),
                    }
                )
        if loan["loan_status"] in {"OVERDUE", "DEFAULTED"}:
            collections.append(
                {
                    "collection_id": f"COL{idx:07d}",
                    "loan_id": loan["loan_id"],
                    "customer_id": loan["customer_id"],
                    "collector_id": f"AGT{random.randint(1, 12):03d}",
                    "action_date": _iso(today - timedelta(days=random.randint(1, 75))),
                    "action_type": random.choice(["call", "sms", "field_visit", "promise_to_pay"]),
                    "amount_recovered": money(amount * Decimal(random.choice(["0.00", "0.02", "0.05", "0.08"]))),
                    "outcome": random.choice(["contacted", "no_response", "promise_to_pay", "paid_partial"]),
                }
            )

    transactions: list[dict[str, str]] = []
    fraud_alerts: list[dict[str, str]] = []
    for idx in range(1, customer_count * 4 + 1):
        customer = random.choice(customers[:customer_count])
        txn_date = today - timedelta(days=random.randint(0, 120))
        txn_type = random.choice(["cash_in", "cash_out", "transfer", "merchant_payment", "loan_repayment"])
        amount = Decimal(random.randint(100, 180000))
        transaction_id = f"TXN{idx:08d}"
        transactions.append(
            {
                "transaction_id": transaction_id,
                "customer_id": customer["customer_id"],
                "transaction_date": _iso(txn_date),
                "transaction_type": txn_type,
                "amount": money(amount),
                "channel": random.choice(["mobile_app", "ussd", "agent", "merchant"]),
                "merchant_category": random.choice(["retail", "utilities", "transport", "cash", "airtime"]),
            }
        )
        if amount >= Decimal("150000") or (txn_type == "cash_out" and amount >= Decimal("90000")):
            fraud_alerts.append(
                {
                    "alert_id": f"ALT{idx:08d}",
                    "transaction_id": transaction_id,
                    "customer_id": customer["customer_id"],
                    "alert_timestamp": _iso(txn_date),
                    "rule_name": "large_or_risky_cash_movement",
                    "risk_score": str(random.randint(72, 98)),
                    "alert_status": random.choice(["OPEN", "REVIEWED", "ESCALATED"]),
                }
            )

    write_csv(paths.source / "branches.csv", BRANCHES)
    write_csv(paths.source / "products.csv", PRODUCTS)
    write_csv(paths.source / "customers.csv", customers)
    write_csv(paths.source / "loans.csv", loans)
    write_csv(paths.source / "repayments.csv", repayments)
    write_csv(paths.source / "mobile_transactions.csv", transactions)
    write_csv(paths.source / "collections.csv", collections)
    write_csv(paths.source / "fraud_alerts.csv", fraud_alerts)
