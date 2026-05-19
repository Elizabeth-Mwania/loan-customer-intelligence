"""Small IO and data helpers used across the platform."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(
    path: Path,
    rows: Iterable[dict[str, object]],
    fieldnames: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized = [dict(row) for row in rows]
    if fieldnames is None:
        fieldnames = []
        for row in materialized:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialized)


def append_jsonl(path: Path, records: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def clean_text(value: object) -> str:
    return str(value or "").strip()


def parse_decimal(value: object, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(clean_text(value))
    except (InvalidOperation, ValueError):
        return default


def money(value: Decimal | float | int | str) -> str:
    return f"{parse_decimal(value):.2f}"


def date_key(value: str) -> str:
    return clean_text(value).replace("-", "")


def dedupe_by_key(rows: Iterable[dict[str, str]], key: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    duplicates: list[dict[str, str]] = []
    for row in rows:
        value = clean_text(row.get(key))
        if value and value not in seen:
            seen.add(value)
            unique.append(row)
        else:
            duplicate = dict(row)
            duplicate["error_reason"] = f"duplicate_or_missing_{key}"
            duplicates.append(duplicate)
    return unique, duplicates
