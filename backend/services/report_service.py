"""
CSV import/export and reporting business logic.

Same (success, message, data) tuple contract as the rest of the backend.
"""

import csv
from backend.repositories.user_repository import UserRepository
from backend.repositories.transaction_repository import TransactionRepository
from backend.services.transaction_service import is_valid_amount, is_valid_date, add_transaction

_user_repo = UserRepository()
_txn_repo = TransactionRepository()

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

    rows = _txn_repo.get_transactions(user_id)
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
# Import
# ---------------------------------------------------------------------------

def import_transactions_csv(user_email: str, file_path: str):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return False, "User not found.", None

    try:
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except OSError as e:
        return False, f"Could not read file: {e}", None
    except csv.Error as e:
        return False, f"Invalid CSV file: {e}", None

    if not rows:
        return False, "CSV file is empty.", None

    missing_cols = [c for c in ("type", "category", "amount", "date") if c not in (reader.fieldnames or [])]
    if missing_cols:
        return False, f"CSV is missing required column(s): {', '.join(missing_cols)}.", None

    imported = 0
    errors = []

    for i, row in enumerate(rows, start=2):  # start=2: row 1 is the header
        txn_type = (row.get("type") or "").strip().lower()
        category = (row.get("category") or "").strip()
        amount = row.get("amount")
        date_str = (row.get("date") or "").strip()
        note = (row.get("note") or "").strip()

        if txn_type not in ("income", "expense"):
            errors.append(f"Row {i}: invalid type '{txn_type}' (must be income or expense).")
            continue
        ok, _ = is_valid_amount(amount)
        if not ok:
            errors.append(f"Row {i}: invalid amount '{amount}'.")
            continue
        if not category:
            errors.append(f"Row {i}: missing category.")
            continue
        if not is_valid_date(date_str):
            errors.append(f"Row {i}: invalid date '{date_str}' (expected YYYY-MM-DD).")
            continue

        success, message, _ = add_transaction(user_email, txn_type, amount, category, date_str, note)
        if success:
            imported += 1
        else:
            errors.append(f"Row {i}: {message}")

    skipped = len(rows) - imported
    message = f"Imported {imported} of {len(rows)} rows."
    if skipped:
        message += f" {skipped} skipped."

    return imported > 0 or not errors, message, {
        "imported": imported, "skipped": skipped, "errors": errors,
    }


# ---------------------------------------------------------------------------
# Reports (FR-11: filters, tables)
# ---------------------------------------------------------------------------

def get_report_transactions(user_email: str, start_date: str = None, end_date: str = None,
                             txn_type: str = None, category: str = None):
    user_id = _user_id_for(user_email)
    if user_id is None:
        return []

    rows = _txn_repo.get_transactions(user_id, txn_type, category)
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