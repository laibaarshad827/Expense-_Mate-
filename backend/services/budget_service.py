"""
Budget business logic: set/get budgets, monthly spending, the monthly budget
summary (status), alerts and suggested budgets.

Layer rules: no SQL here and no format checks. The clock is injected so the
"current month" logic can be tested without waiting for a real month to pass.
"""

from datetime import date

from backend.errors import ServiceError


class BudgetService:

    def __init__(self, user_repo, category_repo, budget_repo, today=date.today):
        self._users = user_repo
        self._categories = category_repo
        self._budgets = budget_repo
        self._today = today

    def _find_user_id(self, user_email):
        user = self._users.get_by_email(user_email)
        return user.user_id if user else None

    def _current_month(self):
        return self._today().strftime("%Y-%m")

    # ---- single budget ----
    def set_budget(self, user_email, category, limit):
        user_id = self._find_user_id(user_email)
        if user_id is None:
            raise ServiceError("User not found.")
        self._budgets.upsert_budget(user_id, category, limit)
        return {"category": category, "limit": limit}

    def get_budget(self, user_email, category):
        user_id = self._find_user_id(user_email)
        return None if user_id is None else self._budgets.get_budget(user_id, category)

    def get_category_spent(self, user_email, category, month=None):
        user_id = self._find_user_id(user_email)
        if user_id is None:
            return 0.0
        return round(self._budgets.get_category_spent(user_id, category, month or self._current_month()), 2)

    # ---- suggestions ----
    @staticmethod
    def _average_of_last_three(monthly):
        """Average of the last 3 months that had spending, or None without history."""
        if not monthly:
            return None
        last_months = sorted(monthly)[-3:]
        return round(sum(monthly[m] for m in last_months) / len(last_months), 2)

    def suggest_budget(self, user_email, category):
        user_id = self._find_user_id(user_email)
        if user_id is None:
            return None
        return self._average_of_last_three(self._budgets.get_monthly_spending_history(user_id, category))

    # ---- monthly budget summary ----
    @staticmethod
    def _summarise(category, limit, spent, history):
        return {
            "category": category,
            "limit": limit,
            "spent": spent,
            "remaining": round(limit - spent, 2) if limit else None,
            "percent": round((spent / limit) * 100, 1) if limit else None,
            "over_budget": bool(limit and spent > limit),
            "suggested": None if limit else BudgetService._average_of_last_three(history),
        }

    def get_budget_status(self, user_email):
        user_id = self._find_user_id(user_email)
        if user_id is None:
            return []

        budgets = self._budgets.get_all_budgets(user_id)
        spent_by_category = self._budgets.get_spent_by_category(user_id, self._current_month())
        history = self._budgets.get_spending_history_by_category(user_id)
        categories = sorted(set(self._categories.get_categories("expense")) | set(budgets))

        return [
            self._summarise(cat, budgets.get(cat), round(spent_by_category.get(cat, 0), 2), history.get(cat))
            for cat in categories
        ]

    def get_budget_alerts(self, user_email):
        return [s for s in self.get_budget_status(user_email) if s["over_budget"]]