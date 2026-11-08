"""
Budget controller: validates basic input, calls BudgetService, returns the
(success, message, data) response. No SQL and no repositories here.
"""

from backend.controllers.common import ok, fail
from backend.errors import ServiceError
from backend.repositories.budget_repository import BudgetRepository
from backend.repositories.transaction_repository import CategoryRepository
from backend.repositories.user_repository import UserRepository
from backend.services.budget_service import BudgetService
from backend.validators import is_valid_amount

__all__ = [
    "set_budget", "get_budget", "get_category_spent", "suggest_budget",
    "get_budget_status", "get_budget_alerts",
]

_service = BudgetService(UserRepository(), CategoryRepository(), BudgetRepository())


def set_budget(user_email, category, limit):
    valid, clean_limit = is_valid_amount(limit)
    if not valid:
        return fail("Please enter a valid budget amount greater than 0.")
    try:
        return ok("Budget saved.", _service.set_budget(user_email, category, clean_limit))
    except ServiceError as error:
        return fail(str(error))


def get_budget(user_email, category):
    return _service.get_budget(user_email, category)


def get_category_spent(user_email, category, month=None):
    return _service.get_category_spent(user_email, category, month)


def suggest_budget(user_email, category):
    return _service.suggest_budget(user_email, category)


def get_budget_status(user_email):
    return _service.get_budget_status(user_email)


def get_budget_alerts(user_email):
    return _service.get_budget_alerts(user_email)