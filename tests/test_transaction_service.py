"""
Unit tests for transaction_service.py (Day 2: Categories + Transactions).
Run with: python -m unittest tests.test_transaction_service -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import init_db, add_day2_tables, DB_PATH
from backend.services.auth_service import register_user, verify_otp
from backend.repositories.user_repository import UserRepository, OtpRepository
from backend.services.transaction_service import (
    get_categories, add_category, is_valid_amount, is_valid_date,
    add_transaction, get_transactions, get_transaction_by_id,
    update_transaction, delete_transaction, get_dashboard_summary,
)


class TestTransactionService(unittest.TestCase):

    def setUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        add_day2_tables()

        # Create and verify one test user for every test to use.
        self.email = "txntest@example.com"
        register_user("Txn Tester", self.email, "pass123", "pass123")
        user_repo = UserRepository()
        otp_repo = OtpRepository()
        user = user_repo.get_by_email(self.email)
        otp = otp_repo.get_latest_otp(user.user_id, "GENERAL")
        verify_otp(self.email, otp.otp_code)

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    # ---------- Validation helpers ----------

    def test_is_valid_amount_accepts_positive_number(self):
        ok, amount = is_valid_amount("150.5")
        self.assertTrue(ok)
        self.assertEqual(amount, 150.5)

    def test_is_valid_amount_rejects_negative(self):
        ok, _ = is_valid_amount("-10")
        self.assertFalse(ok)

    def test_is_valid_amount_rejects_zero(self):
        ok, _ = is_valid_amount("0")
        self.assertFalse(ok)

    def test_is_valid_amount_rejects_non_numeric(self):
        ok, _ = is_valid_amount("abc")
        self.assertFalse(ok)

    def test_is_valid_date_accepts_correct_format(self):
        self.assertTrue(is_valid_date("2026-09-20"))

    def test_is_valid_date_rejects_bad_format(self):
        self.assertFalse(is_valid_date("20-09-2026"))
        self.assertFalse(is_valid_date("not-a-date"))
        self.assertFalse(is_valid_date("2026-13-40"))

    # ---------- Categories ----------

    def test_default_categories_exist(self):
        income = get_categories("income")
        expense = get_categories("expense")
        self.assertIn("Salary", income)
        self.assertIn("Food", expense)

    def test_add_category_success(self):
        success, message, data = add_category("Pets", "expense")
        self.assertTrue(success)
        self.assertIn("Pets", get_categories("expense"))

    def test_add_category_duplicate_fails(self):
        add_category("Pets", "expense")
        success, message, _ = add_category("Pets", "expense")
        self.assertFalse(success)

    def test_add_category_empty_name_fails(self):
        success, _, _ = add_category("   ", "expense")
        self.assertFalse(success)

    def test_add_category_invalid_type_fails(self):
        success, _, _ = add_category("Something", "not-a-type")
        self.assertFalse(success)

    # ---------- Add transaction ----------

    def test_add_transaction_success(self):
        success, message, record = add_transaction(
            self.email, "expense", "250", "Food", "2026-09-20", "Lunch"
        )
        self.assertTrue(success)
        self.assertEqual(record["amount"], 250.0)
        self.assertEqual(record["category"], "Food")
        self.assertEqual(record["date"], "2026-09-20")

    def test_add_transaction_invalid_type_fails(self):
        success, _, _ = add_transaction(self.email, "savings", "100", "Food", "2026-09-20")
        self.assertFalse(success)

    def test_add_transaction_invalid_amount_fails(self):
        success, _, _ = add_transaction(self.email, "expense", "-50", "Food", "2026-09-20")
        self.assertFalse(success)

    def test_add_transaction_missing_category_fails(self):
        success, _, _ = add_transaction(self.email, "expense", "50", "", "2026-09-20")
        self.assertFalse(success)

    def test_add_transaction_invalid_date_fails(self):
        success, _, _ = add_transaction(self.email, "expense", "50", "Food", "not-a-date")
        self.assertFalse(success)

    def test_add_transaction_unknown_user_fails(self):
        success, _, _ = add_transaction("nobody@example.com", "expense", "50", "Food", "2026-09-20")
        self.assertFalse(success)

    # ---------- Get / filter transactions ----------

    def test_get_transactions_returns_all_by_default(self):
        add_transaction(self.email, "income", "5000", "Salary", "2026-09-01")
        add_transaction(self.email, "expense", "200", "Food", "2026-09-02")
        rows = get_transactions(self.email)
        self.assertEqual(len(rows), 2)

    def test_get_transactions_filters_by_type(self):
        add_transaction(self.email, "income", "5000", "Salary", "2026-09-01")
        add_transaction(self.email, "expense", "200", "Food", "2026-09-02")
        rows = get_transactions(self.email, txn_type="income")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["type"], "income")

    def test_get_transactions_filters_by_category(self):
        add_transaction(self.email, "expense", "200", "Food", "2026-09-02")
        add_transaction(self.email, "expense", "100", "Transport", "2026-09-03")
        rows = get_transactions(self.email, category="Food")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["category"], "Food")

    def test_get_transaction_by_id_found(self):
        _, _, record = add_transaction(self.email, "expense", "200", "Food", "2026-09-02")
        found = get_transaction_by_id(self.email, record["id"])
        self.assertIsNotNone(found)
        self.assertEqual(found["id"], record["id"])

    def test_get_transaction_by_id_not_found(self):
        found = get_transaction_by_id(self.email, 99999)
        self.assertIsNone(found)

    # ---------- Update / delete ----------

    def test_update_transaction_success(self):
        _, _, record = add_transaction(self.email, "expense", "200", "Food", "2026-09-02")
        success, message, updated = update_transaction(
            self.email, record["id"], "300", "Food", "2026-09-03", "Updated note"
        )
        self.assertTrue(success)
        self.assertEqual(updated["amount"], 300.0)
        self.assertEqual(updated["date"], "2026-09-03")

    def test_update_transaction_not_found_fails(self):
        success, _, _ = update_transaction(self.email, 99999, "300", "Food", "2026-09-03")
        self.assertFalse(success)

    def test_update_transaction_invalid_amount_fails(self):
        _, _, record = add_transaction(self.email, "expense", "200", "Food", "2026-09-02")
        success, _, _ = update_transaction(self.email, record["id"], "-5", "Food", "2026-09-02")
        self.assertFalse(success)

    def test_delete_transaction_success(self):
        _, _, record = add_transaction(self.email, "expense", "200", "Food", "2026-09-02")
        success, _, _ = delete_transaction(self.email, record["id"])
        self.assertTrue(success)
        self.assertIsNone(get_transaction_by_id(self.email, record["id"]))

    def test_delete_transaction_not_found_fails(self):
        success, _, _ = delete_transaction(self.email, 99999)
        self.assertFalse(success)

    # ---------- Dashboard summary ----------

    def test_dashboard_summary_empty(self):
        summary = get_dashboard_summary(self.email)
        self.assertEqual(summary["total_income"], 0)
        self.assertEqual(summary["total_expense"], 0)
        self.assertEqual(summary["net_savings"], 0)
        self.assertEqual(summary["transaction_count"], 0)

    def test_dashboard_summary_calculates_correctly(self):
        add_transaction(self.email, "income", "5000", "Salary", "2026-09-01")
        add_transaction(self.email, "expense", "1200", "Food", "2026-09-02")
        summary = get_dashboard_summary(self.email)
        self.assertEqual(summary["total_income"], 5000)
        self.assertEqual(summary["total_expense"], 1200)
        self.assertEqual(summary["net_savings"], 3800)
        self.assertEqual(summary["transaction_count"], 2)


if __name__ == "__main__":
    unittest.main()