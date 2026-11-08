"""
CSV import/export and reporting business logic.

Same (success, message, data) tuple contract as the rest of the backend.
"""

import csv
from backend.repositories.user_repository import UserRepository
from backend.repositories.transaction_repository import CategoryRepository, TransactionRepository
from backend.services.csv_importer import CsvImporter
from backend.services.transaction_service import TransactionService

_user_repo = UserRepository()
_transactions = TransactionService(_user_repo, CategoryRepository(), TransactionRepository())
csv_importer = CsvImporter(_transactions, _user_repo)

CSV_COLUMNS = ["type", "category", "amount", "date", "note"]


def _user_id_for(user_email: str):
    user = _user_repo.get_by_email(user_email)
    return user.user_id if user else None


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_transactions_csv(user_email: str, file_path: str):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    rows = _transactions.get_transactions(user_email)
    try:
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for r in rows:
                writer.writerow({
                    "type": r["type"], "category": r["category"],
                    "amount": r["amount"], "date": r["date"], "note": r["note"],
                })
    except OSError as e:
        return False, f"Could not write file: {e}", None

    return True, f"Exported {len(rows)} transactions.", {"count": len(rows), "file_path": file_path}


# ---------------------------------------------------------------------------
# Reports (FR-11: filters, tables)
# ---------------------------------------------------------------------------

def get_report_transactions(user_email: str, start_date: str = None, end_date: str = None,
                             txn_type: str = None, category: str = None):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return []

    rows = _transactions.get_transactions(user_email, txn_type, category)

    if start_date:
        rows = [r for r in rows if r["date"] >= start_date]
    if end_date:
        rows = [r for r in rows if r["date"] <= end_date]
    return rows


def get_category_breakdown(user_email: str, start_date: str = None, end_date: str = None, txn_type: str = "expense"):
    rows = get_report_transactions(user_email, start_date, end_date, txn_type)
    totals = {}
    for r in rows:
        totals[r["category"]] = totals.get(r["category"], 0) + r["amount"]
    return [{"category": cat, "total": round(total, 2)} for cat, total in sorted(totals.items(), key=lambda x: -x[1])]