"""
Unit tests for budget_service.py (Day 3: Budgets).
Run with: python -m unittest tests.test_budget_service -v
"""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import init_db, add_day2_tables, add_day3_tables, DB_PATH
from backend.services.auth_service import register_user, verify_otp
from backend.repositories.user_repository import UserRepository, OtpRepository
from backend.services.transaction_service import add_transaction
from backend.services.budget_service import (
    set_budget, get_budget, get_category_spent, suggest_budget,
    get_budget_status, get_budget_alerts,
)


class TestBudgetService(unittest.TestCase):

    def setUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        add_day2_tables()
        add_day3_tables()

        self.email = "budgettest@example.com"
        register_user("Budget Tester", self.email, "pass123", "pass123")
        user_repo = UserRepository()
        otp_repo = OtpRepository()
        user = user_repo.get_by_email(self.email)
        otp = otp_repo.get_latest_otp(user.user_id, "GENERAL")
        verify_otp(self.email, otp.otp_code)

        self.this_month = date.today().strftime("%Y-%m")

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    # ---------- Set / get budget ----------

    def test_set_budget_success(self):
        success, message, data = set_budget(self.email, "Food", "5000")
        self.assertTrue(success)
        self.assertEqual(data["limit"], 5000.0)

    def test_set_budget_invalid_amount_fails(self):
        success, _, _ = set_budget(self.email, "Food", "-100")
        self.assertFalse(success)

    def test_set_budget_unknown_user_fails(self):
        success, _, _ = set_budget("nobody@example.com", "Food", "5000")
        self.assertFalse(success)

    def test_get_budget_returns_none_when_unset(self):
        self.assertIsNone(get_budget(self.email, "Transport"))

    def test_get_budget_returns_set_value(self):
        set_budget(self.email, "Food", "5000")
        self.assertEqual(get_budget(self.email, "Food"), 5000.0)

    def test_set_budget_overwrites_existing(self):
        set_budget(self.email, "Food", "5000")
        set_budget(self.email, "Food", "8000")
        self.assertEqual(get_budget(self.email, "Food"), 8000.0)

    # ---------- Category spending ----------

    def test_get_category_spent_zero_with_no_transactions(self):
        self.assertEqual(get_category_spent(self.email, "Food"), 0.0)

    def test_get_category_spent_sums_current_month_expenses(self):
        today = date.today().strftime("%Y-%m-%d")
        add_transaction(self.email, "expense", "300", "Food", today)
        add_transaction(self.email, "expense", "200", "Food", today)
        self.assertEqual(get_category_spent(self.email, "Food"), 500.0)

    def test_get_category_spent_ignores_other_categories(self):
        today = date.today().strftime("%Y-%m-%d")
        add_transaction(self.email, "expense", "300", "Food", today)
        add_transaction(self.email, "expense", "100", "Transport", today)
        self.assertEqual(get_category_spent(self.email, "Food"), 300.0)

    def test_get_category_spent_ignores_income(self):
        today = date.today().strftime("%Y-%m-%d")
        add_transaction(self.email, "income", "5000", "Salary", today)
        self.assertEqual(get_category_spent(self.email, "Salary"), 0.0)

    def test_get_category_spent_specific_month(self):
        add_transaction(self.email, "expense", "300", "Food", "2026-01-15")
        self.assertEqual(get_category_spent(self.email, "Food", month="2026-01"), 300.0)
        self.assertEqual(get_category_spent(self.email, "Food", month="2026-02"), 0.0)

    # ---------- Budget status + alerts ----------

    def test_budget_status_under_budget(self):
        today = date.today().strftime("%Y-%m-%d")
        set_budget(self.email, "Food", "1000")
        add_transaction(self.email, "expense", "300", "Food", today)
        status = get_budget_status(self.email)
        food_status = next(s for s in status if s["category"] == "Food")
        self.assertEqual(food_status["spent"], 300)
        self.assertEqual(food_status["remaining"], 700)
        self.assertFalse(food_status["over_budget"])

    def test_budget_status_over_budget(self):
        today = date.today().strftime("%Y-%m-%d")
        set_budget(self.email, "Food", "500")
        add_transaction(self.email, "expense", "700", "Food", today)
        status = get_budget_status(self.email)
        food_status = next(s for s in status if s["category"] == "Food")
        self.assertTrue(food_status["over_budget"])
        self.assertEqual(food_status["remaining"], -200)

    def test_budget_status_no_limit_set(self):
        status = get_budget_status(self.email)
        food_status = next(s for s in status if s["category"] == "Food")
        self.assertIsNone(food_status["limit"])
        self.assertFalse(food_status["over_budget"])

    def test_get_budget_alerts_only_returns_over_budget(self):
        today = date.today().strftime("%Y-%m-%d")
        set_budget(self.email, "Food", "500")
        set_budget(self.email, "Transport", "500")
        add_transaction(self.email, "expense", "700", "Food", today)   # over
        add_transaction(self.email, "expense", "100", "Transport", today)  # under

        alerts = get_budget_alerts(self.email)
        alert_categories = [a["category"] for a in alerts]
        self.assertIn("Food", alert_categories)
        self.assertNotIn("Transport", alert_categories)

    def test_get_budget_alerts_empty_when_nothing_over(self):
        today = date.today().strftime("%Y-%m-%d")
        set_budget(self.email, "Food", "1000")
        add_transaction(self.email, "expense", "300", "Food", today)
        self.assertEqual(get_budget_alerts(self.email), [])

    # ---------- Suggested budget ----------

    def test_suggest_budget_none_without_history(self):
        self.assertIsNone(suggest_budget(self.email, "Transport"))

    def test_suggest_budget_averages_past_months(self):
        add_transaction(self.email, "expense", "300", "Food", "2026-06-10")
        add_transaction(self.email, "expense", "500", "Food", "2026-07-10")
        add_transaction(self.email, "expense", "400", "Food", "2026-08-10")
        suggestion = suggest_budget(self.email, "Food")
        self.assertEqual(suggestion, 400.0)  # (300+500+400)/3


if __name__ == "__main__":
    unittest.main()