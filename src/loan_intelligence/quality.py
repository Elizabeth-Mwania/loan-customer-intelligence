"""Reusable data quality checks for source, silver, and gold datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable

from .utils import clean_text, parse_decimal


@dataclass
class QualityIssue:
    table: str
    check_name: str
    severity: str
    message: str
    failed_count: int


@dataclass
class DataQualityReport:
    run_id: str
    issues: list[QualityIssue] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)

    def add_issue(
        self,
        table: str,
        check_name: str,
        severity: str,
        message: str,
        failed_count: int,
    ) -> None:
        if failed_count > 0:
            self.issues.append(QualityIssue(table, check_name, severity, message, failed_count))

    @property
    def status(self) -> str:
        if any(issue.severity == "error" for issue in self.issues):
            return "failed"
        if self.issues:
            return "passed_with_warnings"
        return "passed"

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "row_counts": self.row_counts,
            "issues": [issue.__dict__ for issue in self.issues],
        }


def missing_required(row: dict[str, str], required_fields: Iterable[str]) -> list[str]:
    return [field for field in required_fields if not clean_text(row.get(field))]


def invalid_positive_decimal(row: dict[str, str], fields: Iterable[str]) -> list[str]:
    invalid: list[str] = []
    for field in fields:
        if parse_decimal(row.get(field)) <= Decimal("0"):
            invalid.append(field)
    return invalid


def invalid_allowed_values(
    row: dict[str, str],
    allowed_values: dict[str, set[str]],
) -> list[str]:
    invalid: list[str] = []
    for field, allowed in allowed_values.items():
        if clean_text(row.get(field)).upper() not in allowed:
            invalid.append(field)
    return invalid


def duplicate_key_count(rows: Iterable[dict[str, str]], key: str) -> int:
    seen: set[str] = set()
    duplicates = 0
    for row in rows:
        value = clean_text(row.get(key))
        if not value:
            continue
        if value in seen:
            duplicates += 1
        else:
            seen.add(value)
    return duplicates


def row_count_reconciles(source_count: int, accepted_count: int, rejected_count: int) -> bool:
    return source_count == accepted_count + rejected_count
