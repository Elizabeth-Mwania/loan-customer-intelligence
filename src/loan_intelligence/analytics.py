"""Analytical helpers used when building gold marts."""

from __future__ import annotations

from decimal import Decimal

from .utils import parse_decimal


def customer_segment(monthly_income: str, defaulted_loans: int = 0) -> str:
    income = parse_decimal(monthly_income)
    if defaulted_loans > 0:
        return "high_risk"
    if income >= Decimal("150000"):
        return "premium"
    if income >= Decimal("70000"):
        return "mass_affluent"
    return "emerging"


def loan_utilization_band(total_disbursed: Decimal) -> str:
    if total_disbursed >= Decimal("1000000"):
        return "high_utilization"
    if total_disbursed >= Decimal("250000"):
        return "moderate_utilization"
    if total_disbursed > Decimal("0"):
        return "low_utilization"
    return "no_loans"


def transaction_risk_score(amount: Decimal, transaction_type: str, recent_alerts: int = 0) -> int:
    score = 20
    if amount >= Decimal("150000"):
        score += 45
    elif amount >= Decimal("80000"):
        score += 25
    if transaction_type.lower() == "cash_out":
        score += 15
    score += min(recent_alerts * 5, 20)
    return min(score, 99)
