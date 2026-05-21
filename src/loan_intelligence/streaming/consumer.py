"""Fraud detection consumer for simulated transaction streams."""

from __future__ import annotations

from decimal import Decimal

from ..analytics import transaction_risk_score
from ..config import PlatformPaths, default_paths
from ..utils import append_jsonl, parse_decimal, read_jsonl, utc_now_iso


def detect_fraud_alerts(
    paths: PlatformPaths | None = None,
    threshold: int = 75,
) -> list[dict[str, object]]:
    paths = paths or default_paths()
    paths.ensure()
    events = read_jsonl(paths.stream / "transactions.jsonl")
    existing_alerts = read_jsonl(paths.stream / "fraud_alerts.jsonl")
    existing_alert_ids = {str(alert.get("alert_id")) for alert in existing_alerts}
    alerts: list[dict[str, object]] = []
    customer_alert_counts: dict[str, int] = {}
    for event in events:
        customer_id = str(event.get("customer_id", ""))
        amount = parse_decimal(event.get("amount"))
        score = transaction_risk_score(amount, str(event.get("transaction_type", "")), customer_alert_counts.get(customer_id, 0))
        if score >= threshold:
            alert_id = f"STREAM-{event.get('event_id')}"
            if alert_id in existing_alert_ids:
                continue
            rule = "high_value_transaction"
            if str(event.get("transaction_type", "")).lower() == "cash_out" and amount >= Decimal("80000"):
                rule = "risky_cash_out"
            alert = {
                "alert_id": alert_id,
                "transaction_id": event.get("transaction_id"),
                "customer_id": customer_id,
                "alert_time": utc_now_iso(),
                "rule_name": rule,
                "risk_score": score,
                "alert_status": "OPEN",
            }
            customer_alert_counts[customer_id] = customer_alert_counts.get(customer_id, 0) + 1
            alerts.append(alert)
            existing_alert_ids.add(alert_id)

    append_jsonl(paths.stream / "fraud_alerts.jsonl", alerts)
    append_jsonl(
        paths.stream / "streaming_logs.jsonl",
        [
            {
                "event_time": utc_now_iso(),
                "events_processed": len(events),
                "alerts_emitted": len(alerts),
                "threshold": threshold,
            }
        ],
    )
    return alerts
