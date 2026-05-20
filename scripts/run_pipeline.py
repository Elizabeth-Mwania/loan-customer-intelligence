from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from loan_intelligence.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["--root", str(ROOT), "run-etl"]))
