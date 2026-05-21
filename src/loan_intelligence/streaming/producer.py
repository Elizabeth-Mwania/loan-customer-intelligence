"""Transaction event producer used for local fraud streaming simulation."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from decimal import Decimal

from ..config import PlatformPaths, default_paths
from ..utils import append_jsonl, money, read_csv


def produce_transactions(
    paths: PlatformPaths | None = None,
    event_count: int = 50,
    seed: int = 7,
) -> list[dict[str, object]]:
    paths = paths or default_paths()
    paths.ensure()
    random.seed(seed)
    customers = read_csv(paths.silver / "customers.csv") or read_csv(paths.source / "customers.csv")
    customer_ids = [row["customer_id"] for row in customers if row.get("customer_id")]
    if not customer_ids:
        customer_ids = ["CUST000001"]

    events: list[dict[str, object]] = []
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    for idx in range(1, event_count + 1):
        amount = Decimal(random.randint(100, 250000))
        event = {
            "event_id": f"EVT{run_stamp}{idx:05d}",
            "transaction_id": f"RT{run_stamp}{idx:05d}",
            "customer_id": random.choice(customer_ids),
            "event_time": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "transaction_type": random.choice(["cash_in", "cash_out", "transfer", "merchant_payment"]),
            "amount": money(amount),
            "channel": random.choice(["mobile_app", "ussd", "agent", "merchant"]),
            "merchant_category": random.choice(["retail", "utilities", "transport", "cash", "airtime"]),
        }
        events.append(event)

    append_jsonl(paths.stream / "transactions.jsonl", events)
    return events
