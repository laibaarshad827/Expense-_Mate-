"""
Category + Transaction business logic.
Function names, parameters, and return format match the frontend's
contract file (backend_interface.py) exactly.
"""

from datetime import date
from backend.repositories.user_repository import UserRepository
from backend.repositories.transaction_repository import CategoryRepository, TransactionRepository

_user_repo = UserRepository()
_category_repo = CategoryRepository()
_txn_repo = TransactionRepository()


def is_valid_amount(amount_str):
    try:
        amount = float(amount_str)
    except (TypeError, ValueError):
        return False, None
    if amount <= 0:
        return False, None
    return True, round(amount, 2)


def is_valid_date(date_str: str) -> bool:
    try:
        year, month, day = (int(part) for part in date_str.split("-"))
        date(year, month, day)
        return True
    except Exception:
        return False


def _user_id_for(user_email: str):
    user = _user_repo.get_by_email(user_email)
    return user.user_id if user else None


def get_categories(txn_type: str):
    return _category_repo.get_categories(txn_type)


def add_category(name: str, txn_type: str):
    name = (name or "").strip()
    if not name:
        return False, "Category name cannot be empty.", None
    if txn_type not in ("income", "expense"):
        return False, "Invalid category type.", None
    if _category_repo.category_exists(name, txn_type):
        return False, "That category already exists.", None

    _category_repo.add_category(name, txn_type)
    return True, "Category added.", {"name": name}


def add_transaction(user_email: str, txn_type: str, amount, category: str, txn_date: str, note: str = ""):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    if txn_type not in ("income", "expense"):
        return False, "Invalid transaction type.", None

    ok, clean_amount = is_valid_amount(amount)
    if not ok:
        return False, "Please enter a valid amount greater than 0.", None

    if not category or not category.strip():
        return False, "Please select a category.", None

    txn_date = (txn_date or "").strip()
    if not is_valid_date(txn_date):
        return False, "Please enter a valid date in YYYY-MM-DD format.", None

    txn_id = _txn_repo.create_transaction(user_id, txn_type, clean_amount, category, txn_date, (note or "").strip())
    record = _txn_repo.get_by_id(user_id, txn_id)
    return True, "Transaction added successfully.", record


def get_transactions(user_email: str, txn_type: str = None, category: str = None):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return []
    return _txn_repo.get_transactions(user_id, txn_type, category)


def get_transaction_by_id(user_email: str, txn_id: int):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return None
    return _txn_repo.get_by_id(user_id, txn_id)


def update_transaction(user_email: str, txn_id: int, amount, category: str, txn_date: str, note: str = ""):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    record = _txn_repo.get_by_id(user_id, txn_id)
    if record is None:
        return False, "Transaction not found.", None

    ok, clean_amount = is_valid_amount(amount)
    if not ok:
        return False, "Please enter a valid amount greater than 0.", None

    if not category or not category.strip():
        return False, "Please select a category.", None

    txn_date = (txn_date or "").strip()
    if not is_valid_date(txn_date):
        return False, "Please enter a valid date in YYYY-MM-DD format.", None

    _txn_repo.update_transaction(txn_id, clean_amount, category, txn_date, (note or "").strip())
    updated = _txn_repo.get_by_id(user_id, txn_id)
    return True, "Transaction updated successfully.", updated


def delete_transaction(user_email: str, txn_id: int):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    deleted = _txn_repo.delete_transaction(user_id, txn_id)
    if not deleted:
        return False, "Transaction not found.", None
    return True, "Transaction deleted.", None


def get_dashboard_summary(user_email: str):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return {"total_income": 0, "total_expense": 0, "net_savings": 0, "transaction_count": 0}

    totals = _txn_repo.get_totals(user_id)
    net = round(totals["total_income"] - totals["total_expense"], 2)
    return {
        "total_income": round(totals["total_income"], 2),
        "total_expense": round(totals["total_expense"], 2),
        "net_savings": net,
        "transaction_count": totals["transaction_count"],
    }