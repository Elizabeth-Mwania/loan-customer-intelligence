from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from loan_intelligence.config import default_paths
from loan_intelligence.etl import LoanIntelligencePipeline
from loan_intelligence.generate_sources import generate_all
from loan_intelligence.streaming.consumer import detect_fraud_alerts
from loan_intelligence.streaming.producer import produce_transactions


class PipelineTests(unittest.TestCase):
    def test_pipeline_builds_required_gold_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = default_paths(temp_dir)
            generate_all(paths, customer_count=25, seed=101)
            result = LoanIntelligencePipeline(paths).run(generate_if_missing=False)

            self.assertIn(result.status, {"passed", "passed_with_warnings"})
            for table in [
                "dim_customer",
                "dim_product",
                "dim_branch",
                "dim_date",
                "dim_loan_status",
                "fact_loan_disbursement",
                "fact_repayments",
                "fact_collections",
                "fact_transactions",
                "portfolio_summary",
            ]:
                self.assertTrue((paths.gold / f"{table}.csv").exists(), table)

            self.assertGreater(result.report.row_counts["gold.fact_loan_disbursement"], 0)
            self.assertGreater(result.report.row_counts["quarantine.customers"], 0)

    def test_streaming_simulation_emits_alerts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = default_paths(temp_dir)
            generate_all(paths, customer_count=20, seed=202)
            LoanIntelligencePipeline(paths).run(generate_if_missing=False)
            events = produce_transactions(paths, event_count=30, seed=303)
            alerts = detect_fraud_alerts(paths, threshold=60)
            duplicate_alerts = detect_fraud_alerts(paths, threshold=60)

            self.assertEqual(len(events), 30)
            self.assertTrue((paths.stream / "transactions.jsonl").exists())
            self.assertTrue((paths.stream / "fraud_alerts.jsonl").exists())
            self.assertGreater(len(alerts), 0)
            self.assertEqual(len(duplicate_alerts), 0)


if __name__ == "__main__":
    unittest.main()
