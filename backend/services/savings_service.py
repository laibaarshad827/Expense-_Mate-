"""
Savings goals business logic: create/update/delete goals, contributions,
and progress calculations.

Same (success, message, data) tuple contract as the rest of the backend,
and same naming style as auth/transaction/budget services.
"""

from backend.repositories.user_repository import UserRepository
from backend.repositories.savings_repository import SavingsRepository
from backend.services.transaction_service import is_valid_amount, is_valid_date

_user_repo = UserRepository()
_savings_repo = SavingsRepository()


def _user_id_for(user_email: str):
    user = _user_repo.get_by_email(user_email)
    return user.user_id if user else None


def _with_progress(goal: dict) -> dict:
    target = goal["target_amount"]
    saved = goal["current_amount"]
    goal["remaining"] = round(target - saved, 2)
    goal["percent"] = round((saved / target) * 100, 1) if target else 0
    goal["is_complete"] = saved >= target
    return goal


def create_savings_goal(user_email: str, goal_name: str, target_amount, deadline: str = None):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    goal_name = (goal_name or "").strip()
    if not goal_name:
        return False, "Goal name cannot be empty.", None

    ok, clean_target = is_valid_amount(target_amount)
    if not ok:
        return False, "Please enter a valid target amount greater than 0.", None

    if deadline:
        deadline = deadline.strip()
        if not is_valid_date(deadline):
            return False, "Please enter a valid deadline in YYYY-MM-DD format.", None

    goal_id = _savings_repo.create_goal(user_id, goal_name, clean_target, deadline)
    goal = _savings_repo.get_by_id(user_id, goal_id)
    return True, "Savings goal created.", _with_progress(goal)


def get_savings_goals(user_email: str):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return []
    goals = _savings_repo.get_all_goals(user_id)
    return [_with_progress(g) for g in goals]


def get_savings_goal_by_id(user_email: str, goal_id: int):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return None
    goal = _savings_repo.get_by_id(user_id, goal_id)
    return _with_progress(goal) if goal else None


def update_savings_goal(user_email: str, goal_id: int, goal_name: str, target_amount, deadline: str = None):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    existing = _savings_repo.get_by_id(user_id, goal_id)
    if existing is None:
        return False, "Savings goal not found.", None

    goal_name = (goal_name or "").strip()
    if not goal_name:
        return False, "Goal name cannot be empty.", None

    ok, clean_target = is_valid_amount(target_amount)
    if not ok:
        return False, "Please enter a valid target amount greater than 0.", None

    if deadline:
        deadline = deadline.strip()
        if not is_valid_date(deadline):
            return False, "Please enter a valid deadline in YYYY-MM-DD format.", None

    _savings_repo.update_goal(goal_id, goal_name, clean_target, deadline)
    updated = _savings_repo.get_by_id(user_id, goal_id)
    return True, "Savings goal updated.", _with_progress(updated)


def delete_savings_goal(user_email: str, goal_id: int):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    deleted = _savings_repo.delete_goal(user_id, goal_id)
    if not deleted:
        return False, "Savings goal not found.", None
    return True, "Savings goal deleted.", None


def add_savings_contribution(user_email: str, goal_id: int, amount):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    goal = _savings_repo.get_by_id(user_id, goal_id)
    if goal is None:
        return False, "Savings goal not found.", None

    ok, clean_amount = is_valid_amount(amount)
    if not ok:
        return False, "Please enter a valid amount greater than 0.", None

    _savings_repo.add_contribution(goal_id, clean_amount)
    updated = _savings_repo.get_by_id(user_id, goal_id)
    return True, "Contribution added.", _with_progress(updated)


def get_savings_summary(user_email: str):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return {"total_target": 0, "total_saved": 0, "goal_count": 0, "overall_percent": 0}

    totals = _savings_repo.get_totals(user_id)
    percent = round((totals["total_saved"] / totals["total_target"]) * 100, 1) if totals["total_target"] else 0
    return {
        "total_target": round(totals["total_target"], 2),
        "total_saved": round(totals["total_saved"], 2),
        "goal_count": totals["goal_count"],
        "overall_percent": percent,
    }