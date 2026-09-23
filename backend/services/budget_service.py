"""
Budget business logic: set/get budgets, spending calculations,
budget status, alerts, and suggested budgets.

Function names, parameters, and return format match the frontend's
contract file (backend_interface.py) exactly.
"""

from datetime import date
from backend.repositories.user_repository import UserRepository
from backend.repositories.transaction_repository import CategoryRepository
from backend.repositories.budget_repository import BudgetRepository
from backend.services.transaction_service import is_valid_amount

_user_repo = UserRepository()
_category_repo = CategoryRepository()
_budget_repo = BudgetRepository()


def _user_id_for(user_email: str):
    user = _user_repo.get_by_email(user_email)
    return user.user_id if user else None


def _current_month() -> str:
    return date.today().strftime("%Y-%m")


def set_budget(user_email: str, category: str, limit):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    ok, clean_limit = is_valid_amount(limit)
    if not ok:
        return False, "Please enter a valid budget amount greater than 0.", None

    _budget_repo.upsert_budget(user_id, category, clean_limit)
    return True, "Budget saved.", {"category": category, "limit": clean_limit}


def get_budget(user_email: str, category: str):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return None
    return _budget_repo.get_budget(user_id, category)


def get_category_spent(user_email: str, category: str, month: str = None) -> float:
    user_id = _user_id_for(user_email)
    if user_id is None:
        return 0.0
    month = month or _current_month()
    return _budget_repo.get_category_spent(user_id, category, month)


def suggest_budget(user_email: str, category: str):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return None

    monthly = _budget_repo.get_monthly_spending_history(user_id, category)
    if not monthly:
        return None

    last_months = sorted(monthly)[-3:]
    return round(sum(monthly[m] for m in last_months) / len(last_months), 2)


def get_budget_status(user_email: str):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return []

    month = _current_month()
    budgets = _budget_repo.get_all_budgets(user_id)
    categories = sorted(set(_category_repo.get_categories("expense")) | set(budgets.keys()))

    statuses = []
    for cat in categories:
        limit = budgets.get(cat)
        spent = _budget_repo.get_category_spent(user_id, cat, month)
        remaining = round(limit - spent, 2) if limit else None
        percent = round((spent / limit) * 100, 1) if limit else None
        statuses.append({
            "category": cat,
            "limit": limit,
            "spent": spent,
            "remaining": remaining,
            "percent": percent,
            "over_budget": bool(limit and spent > limit),
            "suggested": suggest_budget(user_email, cat) if not limit else None,
        })
    return statuses


def get_budget_alerts(user_email: str):
    return [s for s in get_budget_status(user_email) if s["over_budget"]]