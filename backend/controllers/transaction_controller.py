"""
Transaction & category controller.

Receives the action from the screen, validates the BASIC input (required
fields, formats), calls the service, and returns the (success, message, data)
response the screens already understand. No SQL and no repositories here.
"""

from backend.controllers.common import ok, fail
from backend.errors import ServiceError
from backend.repositories.transaction_repository import CategoryRepository, TransactionRepository
from backend.repositories.user_repository import UserRepository
from backend.services.transaction_service import TransactionService
from backend.validators import is_valid_amount, is_valid_date, is_valid_txn_type

__all__ = [
    "get_categories", "add_category", "add_transaction", "get_transactions",
    "get_transaction_by_id", "update_transaction", "delete_transaction",
    "get_dashboard_summary", "is_valid_amount", "is_valid_date",
]

_service = TransactionService(UserRepository(), CategoryRepository(), TransactionRepository())

_BAD_AMOUNT = "Please enter a valid amount greater than 0."
_BAD_CATEGORY = "Please select a category."
_BAD_DATE = "Please enter a valid date in YYYY-MM-DD format."


def get_categories(txn_type):
    return _service.list_categories(txn_type)


def add_category(name, txn_type):
    name = (name or "").strip()
    if not name:
        return fail("Category name cannot be empty.")
    if not is_valid_txn_type(txn_type):
        return fail("Invalid category type.")
    try:
        return ok("Category added.", _service.add_category(name, txn_type))
    except ServiceError as error:
        return fail(str(error))


def add_transaction(user_email, txn_type, amount, category, txn_date, note=""):
    if not is_valid_txn_type(txn_type):
        return fail("Invalid transaction type.")
    valid, clean_amount = is_valid_amount(amount)
    if not valid:
        return fail(_BAD_AMOUNT)
    if not category or not category.strip():
        return fail(_BAD_CATEGORY)
    txn_date = (txn_date or "").strip()
    if not is_valid_date(txn_date):
        return fail(_BAD_DATE)
    try:
        record = _service.add_transaction(user_email, txn_type, clean_amount, category, txn_date, (note or "").strip())
        return ok("Transaction added successfully.", record)
    except ServiceError as error:
        return fail(str(error))


def get_transactions(user_email, txn_type=None, category=None):
    return _service.get_transactions(user_email, txn_type, category)


def get_transaction_by_id(user_email, txn_id):
    return _service.get_transaction(user_email, txn_id)


def update_transaction(user_email, txn_id, amount, category, txn_date, note=""):
    valid, clean_amount = is_valid_amount(amount)
    if not valid:
        return fail(_BAD_AMOUNT)
    if not category or not category.strip():
        return fail(_BAD_CATEGORY)
    txn_date = (txn_date or "").strip()
    if not is_valid_date(txn_date):
        return fail(_BAD_DATE)
    try:
        record = _service.update_transaction(user_email, txn_id, clean_amount, category, txn_date, (note or "").strip())
        return ok("Transaction updated successfully.", record)
    except ServiceError as error:
        return fail(str(error))


def delete_transaction(user_email, txn_id):
    try:
        _service.delete_transaction(user_email, txn_id)
        return ok("Transaction deleted.")
    except ServiceError as error:
        return fail(str(error))


def get_dashboard_summary(user_email):
    return _service.dashboard_summary(user_email)