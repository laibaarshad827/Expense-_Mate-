"""
Unit tests for report_service.py (Day 5: CSV Import/Export + Reports).
Run with: python -m unittest tests.test_report_service -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import init_db, add_day2_tables, DB_PATH
from backend.services.auth_service import register_user, verify_otp
from backend.repositories.user_repository import UserRepository, OtpRepository
from backend.services.transaction_service import add_transaction, get_transactions
from backend.services.report_service import (
    export_transactions_csv, import_transactions_csv,
    get_report_transactions, get_category_breakdown,
)

import tempfile

TEST_EXPORT_PATH = os.path.join(tempfile.gettempdir(), "_unittest_export.csv")
TEST_IMPORT_PATH = os.path.join(tempfile.gettempdir(), "_unittest_import.csv")

class TestReportService(unittest.TestCase):

    def setUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        add_day2_tables()

        self.email = "reporttest@example.com"
        register_user("Report Tester", self.email, "pass123", "pass123")
        user_repo = UserRepository()
        otp_repo = OtpRepository()
        user = user_repo.get_by_email(self.email)
        otp = otp_repo.get_latest_otp(user.user_id, "GENERAL")
        verify_otp(self.email, otp.otp_code)

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        for path in (TEST_EXPORT_PATH, TEST_IMPORT_PATH):
            if os.path.exists(path):
                os.remove(path)

    # ---------- Export ----------

    def test_export_creates_file_with_correct_row_count(self):
        add_transaction(self.email, "expense", "300", "Food", "2026-09-20")
        add_transaction(self.email, "income", "5000", "Salary", "2026-09-01")

        success, message, data = export_transactions_csv(self.email, TEST_EXPORT_PATH)
        self.assertTrue(success)
        self.assertEqual(data["count"], 2)
        self.assertTrue(os.path.exists(TEST_EXPORT_PATH))

        with open(TEST_EXPORT_PATH) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 3)  # header + 2 rows

    def test_export_unknown_user_fails(self):
        success, _, _ = export_transactions_csv("nobody@example.com", TEST_EXPORT_PATH)
        self.assertFalse(success)

    def test_export_with_no_transactions_still_succeeds(self):
        success, message, data = export_transactions_csv(self.email, TEST_EXPORT_PATH)
        self.assertTrue(success)
        self.assertEqual(data["count"], 0)

    # ---------- Import ----------

    def test_import_valid_rows_all_succeed(self):
        with open(TEST_IMPORT_PATH, "w") as f:
            f.write("type,category,amount,date,note\n")
            f.write("expense,Food,250,2026-09-20,Snacks\n")
            f.write("income,Freelance,5000,2026-09-21,Project X\n")

        success, message, data = import_transactions_csv(self.email, TEST_IMPORT_PATH)
        self.assertTrue(success)
        self.assertEqual(data["imported"], 2)
        self.assertEqual(data["skipped"], 0)
        self.assertEqual(len(get_transactions(self.email)), 2)

    def test_import_invalid_amount_row_is_skipped(self):
        with open(TEST_IMPORT_PATH, "w") as f:
            f.write("type,category,amount,date,note\n")
            f.write("expense,Food,-50,2026-09-20,Bad amount\n")

        success, message, data = import_transactions_csv(self.email, TEST_IMPORT_PATH)
        self.assertEqual(data["imported"], 0)
        self.assertEqual(data["skipped"], 1)
        self.assertEqual(len(data["errors"]), 1)

    def test_import_invalid_type_row_is_skipped(self):
        with open(TEST_IMPORT_PATH, "w") as f:
            f.write("type,category,amount,date,note\n")
            f.write("weird,Food,100,2026-09-20,Bad type\n")

        success, message, data = import_transactions_csv(self.email, TEST_IMPORT_PATH)
        self.assertEqual(data["imported"], 0)
        self.assertEqual(data["skipped"], 1)

    def test_import_invalid_date_row_is_skipped(self):
        with open(TEST_IMPORT_PATH, "w") as f:
            f.write("type,category,amount,date,note\n")
            f.write("expense,Food,100,not-a-date,Bad date\n")

        success, message, data = import_transactions_csv(self.email, TEST_IMPORT_PATH)
        self.assertEqual(data["imported"], 0)
        self.assertEqual(data["skipped"], 1)

    def test_import_mixed_valid_and_invalid_rows(self):
        with open(TEST_IMPORT_PATH, "w") as f:
            f.write("type,category,amount,date,note\n")
            f.write("expense,Food,250,2026-09-20,Good row\n")
            f.write("expense,Food,-50,2026-09-20,Bad amount\n")
            f.write("income,Salary,5000,2026-09-01,Good row\n")

        success, message, data = import_transactions_csv(self.email, TEST_IMPORT_PATH)
        self.assertEqual(data["imported"], 2)
        self.assertEqual(data["skipped"], 1)

    def test_import_missing_file_fails(self):
        success, message, _ = import_transactions_csv(self.email, "/tmp/does_not_exist_xyz.csv")
        self.assertFalse(success)

    def test_import_empty_file_fails(self):
        with open(TEST_IMPORT_PATH, "w") as f:
            f.write("")
        success, _, _ = import_transactions_csv(self.email, TEST_IMPORT_PATH)
        self.assertFalse(success)

    def test_import_missing_required_column_fails(self):
        with open(TEST_IMPORT_PATH, "w") as f:
            f.write("category,amount,date\n")  # missing "type"
            f.write("Food,100,2026-09-20\n")
        success, message, _ = import_transactions_csv(self.email, TEST_IMPORT_PATH)
        self.assertFalse(success)

    # ---------- Reports ----------

    def test_get_report_transactions_filters_by_date_range(self):
        add_transaction(self.email, "expense", "100", "Food", "2026-08-15")
        add_transaction(self.email, "expense", "200", "Food", "2026-09-15")
        add_transaction(self.email, "expense", "300", "Food", "2026-10-15")

        rows = get_report_transactions(self.email, start_date="2026-09-01", end_date="2026-09-30")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["amount"], 200)

    def test_get_report_transactions_no_filter_returns_all(self):
        add_transaction(self.email, "expense", "100", "Food", "2026-08-15")
        add_transaction(self.email, "expense", "200", "Food", "2026-09-15")
        rows = get_report_transactions(self.email)
        self.assertEqual(len(rows), 2)

    def test_category_breakdown_sums_correctly(self):
        add_transaction(self.email, "expense", "300", "Food", "2026-09-15")
        add_transaction(self.email, "expense", "200", "Food", "2026-09-16")
        add_transaction(self.email, "expense", "100", "Transport", "2026-09-16")

        breakdown = get_category_breakdown(self.email)
        food_total = next(b["total"] for b in breakdown if b["category"] == "Food")
        self.assertEqual(food_total, 500)

    def test_category_breakdown_sorted_highest_first(self):
        add_transaction(self.email, "expense", "100", "Transport", "2026-09-15")
        add_transaction(self.email, "expense", "500", "Food", "2026-09-15")

        breakdown = get_category_breakdown(self.email)
        self.assertEqual(breakdown[0]["category"], "Food")

    def test_category_breakdown_ignores_income(self):
        add_transaction(self.email, "income", "5000", "Salary", "2026-09-15")
        breakdown = get_category_breakdown(self.email)
        self.assertEqual(breakdown, [])


if __name__ == "__main__":
    unittest.main()