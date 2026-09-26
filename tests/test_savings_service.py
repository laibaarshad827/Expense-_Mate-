"""
Unit tests for savings_service.py (Day 4: Savings Goals).
Run with: python -m unittest tests.test_savings_service -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import init_db, add_day2_tables, add_day4_tables, DB_PATH
from backend.services.auth_service import register_user, verify_otp
from backend.repositories.user_repository import UserRepository, OtpRepository
from backend.services.savings_service import (
    create_savings_goal, get_savings_goals, get_savings_goal_by_id,
    update_savings_goal, delete_savings_goal, add_savings_contribution,
    get_savings_summary,
)


class TestSavingsService(unittest.TestCase):

    def setUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        add_day2_tables()
        add_day4_tables()

        self.email = "savingstest@example.com"
        register_user("Savings Tester", self.email, "pass123", "pass123")
        user_repo = UserRepository()
        otp_repo = OtpRepository()
        user = user_repo.get_by_email(self.email)
        otp = otp_repo.get_latest_otp(user.user_id, "GENERAL")
        verify_otp(self.email, otp.otp_code)

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    # ---------- Create ----------

    def test_create_goal_success(self):
        success, message, goal = create_savings_goal(self.email, "Laptop", "150000", "2027-01-01")
        self.assertTrue(success)
        self.assertEqual(goal["goal_name"], "Laptop")
        self.assertEqual(goal["target_amount"], 150000.0)
        self.assertEqual(goal["current_amount"], 0)
        self.assertEqual(goal["percent"], 0)
        self.assertFalse(goal["is_complete"])

    def test_create_goal_without_deadline(self):
        success, _, goal = create_savings_goal(self.email, "Emergency Fund", "50000")
        self.assertTrue(success)
        self.assertIsNone(goal["deadline"])

    def test_create_goal_empty_name_fails(self):
        success, _, _ = create_savings_goal(self.email, "   ", "1000")
        self.assertFalse(success)

    def test_create_goal_invalid_target_fails(self):
        success, _, _ = create_savings_goal(self.email, "Laptop", "-500")
        self.assertFalse(success)

    def test_create_goal_invalid_deadline_fails(self):
        success, _, _ = create_savings_goal(self.email, "Laptop", "1000", "not-a-date")
        self.assertFalse(success)

    def test_create_goal_unknown_user_fails(self):
        success, _, _ = create_savings_goal("nobody@example.com", "Laptop", "1000")
        self.assertFalse(success)

    # ---------- Get ----------

    def test_get_savings_goals_empty_initially(self):
        self.assertEqual(get_savings_goals(self.email), [])

    def test_get_savings_goals_returns_all(self):
        create_savings_goal(self.email, "Laptop", "150000")
        create_savings_goal(self.email, "Emergency Fund", "50000")
        goals = get_savings_goals(self.email)
        self.assertEqual(len(goals), 2)

    def test_get_goal_by_id_found(self):
        _, _, goal = create_savings_goal(self.email, "Laptop", "150000")
        found = get_savings_goal_by_id(self.email, goal["goal_id"])
        self.assertIsNotNone(found)
        self.assertEqual(found["goal_name"], "Laptop")

    def test_get_goal_by_id_not_found(self):
        self.assertIsNone(get_savings_goal_by_id(self.email, 99999))

    # ---------- Update ----------

    def test_update_goal_success(self):
        _, _, goal = create_savings_goal(self.email, "Laptop", "150000")
        success, _, updated = update_savings_goal(
            self.email, goal["goal_id"], "New Laptop", "160000", "2027-03-01"
        )
        self.assertTrue(success)
        self.assertEqual(updated["goal_name"], "New Laptop")
        self.assertEqual(updated["target_amount"], 160000.0)

    def test_update_goal_not_found_fails(self):
        success, _, _ = update_savings_goal(self.email, 99999, "Laptop", "150000")
        self.assertFalse(success)

    def test_update_goal_invalid_target_fails(self):
        _, _, goal = create_savings_goal(self.email, "Laptop", "150000")
        success, _, _ = update_savings_goal(self.email, goal["goal_id"], "Laptop", "-1")
        self.assertFalse(success)

    # ---------- Delete ----------

    def test_delete_goal_success(self):
        _, _, goal = create_savings_goal(self.email, "Laptop", "150000")
        success, _, _ = delete_savings_goal(self.email, goal["goal_id"])
        self.assertTrue(success)
        self.assertIsNone(get_savings_goal_by_id(self.email, goal["goal_id"]))

    def test_delete_goal_not_found_fails(self):
        success, _, _ = delete_savings_goal(self.email, 99999)
        self.assertFalse(success)

    # ---------- Contributions ----------

    def test_add_contribution_updates_progress(self):
        _, _, goal = create_savings_goal(self.email, "Laptop", "10000")
        success, _, updated = add_savings_contribution(self.email, goal["goal_id"], "4000")
        self.assertTrue(success)
        self.assertEqual(updated["current_amount"], 4000.0)
        self.assertEqual(updated["percent"], 40.0)
        self.assertFalse(updated["is_complete"])

    def test_contribution_marks_goal_complete(self):
        _, _, goal = create_savings_goal(self.email, "Laptop", "10000")
        success, _, updated = add_savings_contribution(self.email, goal["goal_id"], "10000")
        self.assertTrue(updated["is_complete"])

    def test_contribution_accumulates_across_calls(self):
        _, _, goal = create_savings_goal(self.email, "Laptop", "10000")
        add_savings_contribution(self.email, goal["goal_id"], "3000")
        _, _, updated = add_savings_contribution(self.email, goal["goal_id"], "2000")
        self.assertEqual(updated["current_amount"], 5000.0)

    def test_contribution_invalid_amount_fails(self):
        _, _, goal = create_savings_goal(self.email, "Laptop", "10000")
        success, _, _ = add_savings_contribution(self.email, goal["goal_id"], "-100")
        self.assertFalse(success)

    def test_contribution_goal_not_found_fails(self):
        success, _, _ = add_savings_contribution(self.email, 99999, "100")
        self.assertFalse(success)

    # ---------- Summary ----------

    def test_savings_summary_empty(self):
        summary = get_savings_summary(self.email)
        self.assertEqual(summary["goal_count"], 0)
        self.assertEqual(summary["total_target"], 0)
        self.assertEqual(summary["total_saved"], 0)

    def test_savings_summary_aggregates_goals(self):
        _, _, g1 = create_savings_goal(self.email, "Laptop", "10000")
        _, _, g2 = create_savings_goal(self.email, "Trip", "5000")
        add_savings_contribution(self.email, g1["goal_id"], "4000")
        add_savings_contribution(self.email, g2["goal_id"], "1000")

        summary = get_savings_summary(self.email)
        self.assertEqual(summary["goal_count"], 2)
        self.assertEqual(summary["total_target"], 15000)
        self.assertEqual(summary["total_saved"], 5000)
        self.assertAlmostEqual(summary["overall_percent"], 33.3, places=1)


if __name__ == "__main__":
    unittest.main()