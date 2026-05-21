from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from loan_intelligence.quality import duplicate_key_count, missing_required, row_count_reconciles


class QualityTests(unittest.TestCase):
    def test_missing_required_fields_are_reported(self):
        row = {"customer_id": "", "first_name": "Amina", "branch_id": "BR001"}
        self.assertEqual(missing_required(row, ["customer_id", "first_name"]), ["customer_id"])

    def test_duplicate_key_count_ignores_blank_keys(self):
        rows = [
            {"loan_id": "LN1"},
            {"loan_id": "LN1"},
            {"loan_id": ""},
            {"loan_id": "LN2"},
        ]
        self.assertEqual(duplicate_key_count(rows, "loan_id"), 1)

    def test_row_count_reconciliation(self):
        self.assertTrue(row_count_reconciles(10, 8, 2))
        self.assertFalse(row_count_reconciles(10, 7, 2))


if __name__ == "__main__":
    unittest.main()
