"""Shared configuration and filesystem paths for the local platform."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


SOURCE_TABLES = [
    "branches",
    "products",
    "customers",
    "loans",
    "repayments",
    "mobile_transactions",
    "collections",
    "fraud_alerts",
]


@dataclass(frozen=True)
class PlatformPaths:
    """Filesystem contract used by generators, ETL, tests, and docs."""

    root: Path

    @classmethod
    def from_env(cls) -> "PlatformPaths":
        return cls(Path(os.environ.get("LCIP_HOME", Path.cwd())).resolve())

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def source(self) -> Path:
        return self.data / "source"

    @property
    def bronze(self) -> Path:
        return self.data / "bronze"

    @property
    def silver(self) -> Path:
        return self.data / "silver"

    @property
    def gold(self) -> Path:
        return self.data / "gold"

    @property
    def quarantine(self) -> Path:
        return self.data / "quarantine"

    @property
    def stream(self) -> Path:
        return self.data / "stream"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def etl_logs(self) -> Path:
        return self.logs / "etl_runs"

    def ensure(self) -> None:
        for path in [
            self.source,
            self.bronze,
            self.silver,
            self.gold,
            self.quarantine,
            self.stream,
            self.etl_logs,
        ]:
            path.mkdir(parents=True, exist_ok=True)


def default_paths(root: str | Path | None = None) -> PlatformPaths:
    """Return platform paths rooted at `root` or the current workspace."""

    if root is None:
        return PlatformPaths.from_env()
    return PlatformPaths(Path(root).resolve())
