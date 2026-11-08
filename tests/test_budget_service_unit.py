"""
Unit tests for BudgetService (the monthly budget summary) with fake repositories
and a FIXED clock - no database and no dependence on today's real date.
"""
import unittest
from datetime import date
from types import SimpleNamespace

from backend.errors import ServiceError
from backend.services.budget_service import BudgetService


class FakeUsers:
    def get_by_email(self, email):
        return SimpleNamespace(user_id=1) if email == "ana@x.com" else None


class FakeCategories:
    def get_categories(self, t): return ["Food", "Rent", "Transport"]


class FakeBudgets:
    def __init__(self, budgets=None, spent=None, history=None):
        self.budgets, self.spent, self.history = budgets or {}, spent or {}, history or {}
        self.calls = []
    def upsert_budget(self, uid, cat, limit): self.budgets[cat] = limit
    def get_budget(self, uid, cat): return self.budgets.get(cat)
    def get_all_budgets(self, uid): self.calls.append("all"); return dict(self.budgets)
    def get_category_spent(self, uid, cat, month): return self.spent.get(cat, 0)
    def get_spent_by_category(self, uid, month): self.calls.append(("spent", month)); return dict(self.spent)
    def get_monthly_spending_history(self, uid, cat): return self.history.get(cat, {})
    def get_spending_history_by_category(self, uid): self.calls.append("history"); return dict(self.history)


def service(budgets=None, spent=None, history=None, today=date(2026, 3, 15)):
    repo = FakeBudgets(budgets, spent, history)
    return BudgetService(FakeUsers(), FakeCategories(), repo, today=lambda: today), repo


class TestMonthlyBudgetSummary(unittest.TestCase):
    def row(self, rows, cat):
        return next(r for r in rows if r["category"] == cat)

    def test_under_budget_row(self):
        s, _ = service({"Food": 1000}, {"Food": 300})
        r = self.row(s.get_budget_status("ana@x.com"), "Food")
        self.assertEqual((r["limit"], r["spent"], r["remaining"], r["percent"], r["over_budget"]),
                         (1000, 300, 700, 30.0, False))

    def test_over_budget_row_and_alert(self):
        s, _ = service({"Food": 500}, {"Food": 700})
        r = self.row(s.get_budget_status("ana@x.com"), "Food")
        self.assertTrue(r["over_budget"]); self.assertEqual(r["remaining"], -200)
        self.assertEqual([a["category"] for a in s.get_budget_alerts("ana@x.com")], ["Food"])

    def test_exactly_at_limit_is_not_over_budget(self):
        s, _ = service({"Food": 500}, {"Food": 500})
        self.assertFalse(self.row(s.get_budget_status("ana@x.com"), "Food")["over_budget"])

    def test_category_without_budget_gets_suggestion_from_last_three_months(self):
        hist = {"Rent": {"2025-12": 100, "2026-01": 300, "2026-02": 500, "2026-03": 400}}
        s, _ = service(history=hist)
        r = self.row(s.get_budget_status("ana@x.com"), "Rent")
        self.assertIsNone(r["limit"]); self.assertEqual(r["suggested"], 400.0)   # (300+500+400)/3

    def test_budgeted_category_has_no_suggestion(self):
        s, _ = service({"Food": 100}, history={"Food": {"2026-01": 50}})
        self.assertIsNone(self.row(s.get_budget_status("ana@x.com"), "Food")["suggested"])

    def test_uses_the_injected_clock_for_the_current_month(self):
        s, repo = service(today=date(2031, 11, 2))
        s.get_budget_status("ana@x.com")
        self.assertIn(("spent", "2031-11"), repo.calls)

    def test_summary_needs_exactly_three_repository_queries(self):
        s, repo = service({"Food": 1})
        s.get_budget_status("ana@x.com")
        self.assertEqual(len(repo.calls), 3)   # was 1 + one-or-two per category before the refactor

    def test_unknown_user(self):
        s, _ = service()
        self.assertEqual(s.get_budget_status("ghost@x.com"), [])
        with self.assertRaises(ServiceError):
            s.set_budget("ghost@x.com", "Food", 10)


if __name__ == "__main__":
    unittest.main()