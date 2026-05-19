"""Command-line interface for local platform workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import default_paths
from .etl import LoanIntelligencePipeline
from .generate_sources import generate_all
from .streaming.consumer import detect_fraud_alerts
from .streaming.producer import produce_transactions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Loan & Customer Intelligence Platform")
    parser.add_argument("--root", default=None, help="Workspace root. Defaults to LCIP_HOME or the current directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate deterministic source CSV files")
    generate.add_argument("--customers", type=int, default=120)
    generate.add_argument("--seed", type=int, default=42)

    subparsers.add_parser("run-etl", help="Run bronze, silver, gold ETL pipeline")

    reset = subparsers.add_parser("reset-outputs", help="Delete generated bronze/silver/gold/quarantine/stream outputs")
    reset.set_defaults(reset_outputs=True)

    stream = subparsers.add_parser("simulate-stream", help="Produce transaction events and emit fraud alerts")
    stream.add_argument("--events", type=int, default=50)
    stream.add_argument("--threshold", type=int, default=75)
    stream.add_argument("--seed", type=int, default=7)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = default_paths(Path(args.root) if args.root else None)

    if args.command == "generate":
        generate_all(paths, customer_count=args.customers, seed=args.seed)
        print(json.dumps({"status": "generated", "source_dir": str(paths.source)}, indent=2))
        return 0

    if args.command == "run-etl":
        result = LoanIntelligencePipeline(paths).run(generate_if_missing=True)
        print(json.dumps({"status": result.status, "run_id": result.run_id, "audit_log": str(result.audit_log)}, indent=2))
        return 0 if result.status != "failed" else 1

    if args.command == "reset-outputs":
        LoanIntelligencePipeline(paths).reset_outputs()
        print(json.dumps({"status": "outputs_reset"}, indent=2))
        return 0

    if args.command == "simulate-stream":
        events = produce_transactions(paths, event_count=args.events, seed=args.seed)
        alerts = detect_fraud_alerts(paths, threshold=args.threshold)
        print(json.dumps({"events": len(events), "alerts": len(alerts), "stream_dir": str(paths.stream)}, indent=2))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
