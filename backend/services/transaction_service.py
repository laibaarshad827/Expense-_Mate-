"""
Transaction & category business logic.

Layer rules: no SQL here (repositories do that) and no input-format checks
(controllers do that). The service decides things like "does this user exist?",
"does this transaction exist?", and computes the dashboard totals.
"""

from backend.errors import ServiceError


class TransactionService:

    def __init__(self, user_repo, category_repo, txn_repo):
        self._users = user_repo
        self._categories = category_repo
        self._txns = txn_repo

    # ---- helpers ----
    def _find_user_id(self, user_email):
        user = self._users.get_by_email(user_email)
        return user.user_id if user else None

    def _require_user_id(self, user_email):
        user_id = self._find_user_id(user_email)
        if user_id is None:
            raise ServiceError("User not found.")
        return user_id

    # ---- categories ----
    def list_categories(self, txn_type):
        return self._categories.get_categories(txn_type)

    def add_category(self, name, txn_type):
        if self._categories.category_exists(name, txn_type):
            raise ServiceError("That category already exists.")
        self._categories.add_category(name, txn_type)
        return {"name": name}

    # ---- transactions ----
    def add_transaction(self, user_email, txn_type, amount, category, txn_date, note):
        user_id = self._require_user_id(user_email)
        txn_id = self._txns.create_transaction(user_id, txn_type, amount, category, txn_date, note)
        return self._txns.get_by_id(user_id, txn_id).to_record()

    def get_transactions(self, user_email, txn_type=None, category=None):
        user_id = self._find_user_id(user_email)
        if user_id is None:
            return []
        return [t.to_record() for t in self._txns.get_transactions(user_id, txn_type, category)]

    def get_transaction(self, user_email, txn_id):
        user_id = self._find_user_id(user_email)
        if user_id is None:
            return None
        txn = self._txns.get_by_id(user_id, txn_id)
        return txn.to_record() if txn else None

    def update_transaction(self, user_email, txn_id, amount, category, txn_date, note):
        user_id = self._require_user_id(user_email)
        if self._txns.get_by_id(user_id, txn_id) is None:
            raise ServiceError("Transaction not found.")
        self._txns.update_transaction(txn_id, amount, category, txn_date, note)
        return self._txns.get_by_id(user_id, txn_id).to_record()

    def delete_transaction(self, user_email, txn_id):
        user_id = self._require_user_id(user_email)
        if not self._txns.delete_transaction(user_id, txn_id):
            raise ServiceError("Transaction not found.")

    # ---- dashboard (business calculation lives here, not in the repository) ----
    def dashboard_summary(self, user_email):
        user_id = self._find_user_id(user_email)
        if user_id is None:
            return {"total_income": 0, "total_expense": 0, "net_savings": 0, "transaction_count": 0}
        totals = self._txns.get_totals(user_id)
        return {
            "total_income": round(totals["total_income"], 2),
            "total_expense": round(totals["total_expense"], 2),
            "net_savings": round(totals["total_income"] - totals["total_expense"], 2),
            "transaction_count": totals["transaction_count"],
        }