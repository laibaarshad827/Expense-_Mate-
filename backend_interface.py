"""
backend_interface.py
=====================
THIS FILE IS THE CONTRACT BETWEEN FRONTEND AND BACKEND.

Right now every function below is a MOCK (it stores data in memory using
Python dictionaries) so you can build and test the whole frontend without
waiting for your friend's real SQLite backend to be ready.

HOW THIS WILL BE USED IN THE REAL PROJECT:
  - Your friend will write the real backend (SQLite, password hashing, OTP
    emails, etc.) in her own file(s) (e.g. auth_service.py, db.py).
  - She will keep the EXACT SAME function names, parameters, and return
    format that are defined here.
  - On integration day (Day 6 in your roadmap), you literally replace the
    body of this file with:  "from auth_service import *"
    (or delete this file and import her real module instead)
  - None of your screen files (register_screen.py, login_screen.py, etc.)
    need to change AT ALL, because they only ever call these function
    names, never the database directly.

RETURN FORMAT CONTRACT (every function follows this):
    (success: bool, message: str, data: dict | None)

    success -> True if the operation worked, False otherwise
    message -> a human-readable string to show the user (NFR-6: clear
               error messages for invalid input)
    data    -> extra info if needed (e.g. the user's info after login),
               otherwise None
"""

import re
import random
import itertools
from datetime import date

# ---------------------------------------------------------------------------
# MOCK IN-MEMORY "DATABASE" (your friend will replace this with real SQLite)
# ---------------------------------------------------------------------------
_users = {}          # key: email -> {username, password, ...}
_otp_store = {}       # key: email -> otp_code (as string)
_current_user = {}    # very simple "session" for the mock

# --- Categories & Transactions (Day 2 - FR-3, FR-4, FR-5, FR-6) ------------
DEFAULT_INCOME_CATEGORIES = ["Salary", "Freelance", "Business", "Gift", "Other Income"]
DEFAULT_EXPENSE_CATEGORIES = [
    "Food", "Rent", "Transport", "Utilities", "Shopping",
    "Health", "Education", "Entertainment", "Other Expense",
]

# custom categories the user has created via "+ Add Category" (FR-6)
_custom_categories = {"income": [], "expense": []}

_transactions = {}          # key: user_email -> list[transaction dict]
_txn_id_counter = itertools.count(1)


# ---------------------------------------------------------------------------
# VALIDATION HELPERS (kept here so both mock + real backend can reuse them)
# ---------------------------------------------------------------------------
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email or ""))


def is_valid_password(password: str) -> bool:
    # NFR-7 related: minimum reasonable password strength
    return bool(password) and len(password) >= 6


# ---------------------------------------------------------------------------
# FR-1 / FR-2: Account creation, login, logout
# ---------------------------------------------------------------------------
def register_user(username: str, email: str, password: str, confirm_password: str):
    if not username or not username.strip():
        return False, "Username cannot be empty.", None
    if not is_valid_email(email):
        return False, "Please enter a valid email address.", None
    if not is_valid_password(password):
        return False, "Password must be at least 6 characters long.", None
    if password != confirm_password:
        return False, "Passwords do not match.", None
    if email in _users:
        return False, "An account with this email already exists.", None

    # NFR-7: never store plain text password (mock uses a fake "hash")
    _users[email] = {
        "username": username.strip(),
        "email": email,
        "password_hash": f"hashed:{password}",
    }
    send_otp(email)  # auto-send OTP right after registering
    return True, "Account created. Please verify the OTP sent to your email.", {"email": email}


def send_otp(email: str):
    if email not in _users:
        return False, "No account found with this email.", None
    otp_code = f"{random.randint(100000, 999999)}"
    _otp_store[email] = otp_code
    # In the real backend this will actually email the OTP.
    print(f"[MOCK OTP] OTP for {email} is: {otp_code}")
    return True, "OTP sent successfully. Check console (mock mode).", None


def verify_otp(email: str, otp_code: str):
    if not otp_code or not otp_code.strip():
        return False, "Please enter the OTP.", None
    real_otp = _otp_store.get(email)
    if real_otp is None:
        return False, "No OTP was requested for this email.", None
    if otp_code.strip() != real_otp:
        return False, "Incorrect OTP. Please try again.", None
    del _otp_store[email]
    return True, "OTP verified successfully.", None


def login_user(email: str, password: str):
    if not is_valid_email(email):
        return False, "Please enter a valid email address.", None
    user = _users.get(email)
    if user is None:
        return False, "No account found with this email.", None
    if user["password_hash"] != f"hashed:{password}":
        return False, "Incorrect password.", None
    _current_user["email"] = email
    return True, "Login successful.", {"username": user["username"], "email": email}


def logout_user():
    _current_user.clear()
    return True, "Logged out successfully.", None


# ---------------------------------------------------------------------------
# Forgot / Reset password
# ---------------------------------------------------------------------------
def request_password_reset(email: str):
    if email not in _users:
        return False, "No account found with this email.", None
    return send_otp(email)


def reset_password(email: str, otp_code: str, new_password: str, confirm_password: str):
    ok, msg, _ = verify_otp(email, otp_code)
    if not ok:
        return False, msg, None
    if not is_valid_password(new_password):
        return False, "Password must be at least 6 characters long.", None
    if new_password != confirm_password:
        return False, "Passwords do not match.", None
    _users[email]["password_hash"] = f"hashed:{new_password}"
    return True, "Password reset successfully. You can now log in.", None


# ---------------------------------------------------------------------------
# Update password / update email (while logged in)
# ---------------------------------------------------------------------------
def update_password(email: str, old_password: str, new_password: str, confirm_password: str):
    user = _users.get(email)
    if user is None:
        return False, "User not found.", None
    if user["password_hash"] != f"hashed:{old_password}":
        return False, "Current password is incorrect.", None
    if not is_valid_password(new_password):
        return False, "New password must be at least 6 characters long.", None
    if new_password != confirm_password:
        return False, "New passwords do not match.", None
    user["password_hash"] = f"hashed:{new_password}"
    return True, "Password updated successfully.", None


def update_email(old_email: str, new_email: str, otp_code: str):
    if not is_valid_email(new_email):
        return False, "Please enter a valid new email address.", None
    if new_email in _users:
        return False, "This email is already in use.", None
    ok, msg, _ = verify_otp(old_email, otp_code)
    if not ok:
        return False, msg, None
    user = _users.pop(old_email)
    user["email"] = new_email
    _users[new_email] = user
    return True, "Email updated successfully.", {"email": new_email}


# ---------------------------------------------------------------------------
# FR-5 / FR-6: Categories (income & expense, plus user-defined custom ones)
# ---------------------------------------------------------------------------
def get_categories(txn_type: str):
    """Returns the list of category names available for 'income' or
    'expense' (defaults + anything the user added with add_category)."""
    if txn_type == "income":
        return DEFAULT_INCOME_CATEGORIES + _custom_categories["income"]
    return DEFAULT_EXPENSE_CATEGORIES + _custom_categories["expense"]


def add_category(name: str, txn_type: str):
    name = (name or "").strip()
    if not name:
        return False, "Category name cannot be empty.", None
    if txn_type not in ("income", "expense"):
        return False, "Invalid category type.", None
    existing = get_categories(txn_type)
    if name.lower() in [c.lower() for c in existing]:
        return False, "That category already exists.", None
    _custom_categories[txn_type].append(name)
    return True, "Category added.", {"name": name}


# ---------------------------------------------------------------------------
# FR-3 / FR-4: Add / edit / delete transactions (income & expense)
# ---------------------------------------------------------------------------
def is_valid_amount(amount_str: str):
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


def add_transaction(user_email: str, txn_type: str, amount, category: str, txn_date: str, note: str = ""):
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

    txn_id = next(_txn_id_counter)
    record = {
        "id": txn_id,
        "type": txn_type,             # "income" | "expense"
        "amount": clean_amount,
        "category": category,
        "date": txn_date,
        "note": (note or "").strip(),
    }
    _transactions.setdefault(user_email, []).append(record)
    return True, "Transaction added successfully.", record


def get_transactions(user_email: str, txn_type: str = None, category: str = None):
    """Returns transactions for a user, newest date first. Optional
    filters for FR-13 (filter by type/category)."""
    rows = list(_transactions.get(user_email, []))
    if txn_type and txn_type != "All":
        rows = [r for r in rows if r["type"] == txn_type]
    if category and category != "All":
        rows = [r for r in rows if r["category"] == category]
    rows.sort(key=lambda r: (r["date"], r["id"]), reverse=True)
    return rows


def get_transaction_by_id(user_email: str, txn_id: int):
    for r in _transactions.get(user_email, []):
        if r["id"] == txn_id:
            return r
    return None


def update_transaction(user_email: str, txn_id: int, amount, category: str, txn_date: str, note: str = ""):
    record = get_transaction_by_id(user_email, txn_id)
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

    record["amount"] = clean_amount
    record["category"] = category
    record["date"] = txn_date
    record["note"] = (note or "").strip()
    return True, "Transaction updated successfully.", record


def delete_transaction(user_email: str, txn_id: int):
    rows = _transactions.get(user_email, [])
    for i, r in enumerate(rows):
        if r["id"] == txn_id:
            rows.pop(i)
            return True, "Transaction deleted.", None
    return False, "Transaction not found.", None


# ---------------------------------------------------------------------------
# FR-12: Dashboard / monthly summary calculations
# ---------------------------------------------------------------------------
def get_dashboard_summary(user_email: str):
    rows = _transactions.get(user_email, [])
    total_income = sum(r["amount"] for r in rows if r["type"] == "income")
    total_expense = sum(r["amount"] for r in rows if r["type"] == "expense")
    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_savings": round(total_income - total_expense, 2),
        "transaction_count": len(rows),
    }


# ---------------------------------------------------------------------------
# FR-7 / FR-8 / FR-9 / FR-10: Monthly budgets per expense category
# ---------------------------------------------------------------------------
_budgets = {}  # key: user_email -> {category: monthly_limit}


def _month_key(d: str) -> str:
    return d[:7]  # "YYYY-MM"


def _current_month() -> str:
    return date.today().strftime("%Y-%m")


def set_budget(user_email: str, category: str, limit):
    ok, clean_limit = is_valid_amount(limit)
    if not ok:
        return False, "Please enter a valid budget amount greater than 0.", None
    _budgets.setdefault(user_email, {})[category] = clean_limit
    return True, "Budget saved.", {"category": category, "limit": clean_limit}


def get_budget(user_email: str, category: str):
    return _budgets.get(user_email, {}).get(category)


def get_category_spent(user_email: str, category: str, month: str = None) -> float:
    month = month or _current_month()
    return round(sum(
        r["amount"] for r in _transactions.get(user_email, [])
        if r["type"] == "expense" and r["category"] == category and _month_key(r["date"]) == month
    ), 2)


def suggest_budget(user_email: str, category: str):
    """FR-8: average of the last 3 months that actually have spending in
    this category. Returns None if there isn't enough history yet."""
    monthly = {}
    for r in _transactions.get(user_email, []):
        if r["type"] == "expense" and r["category"] == category:
            monthly[_month_key(r["date"])] = monthly.get(_month_key(r["date"]), 0) + r["amount"]
    if not monthly:
        return None
    last_months = sorted(monthly)[-3:]
    return round(sum(monthly[m] for m in last_months) / len(last_months), 2)


def get_budget_status(user_email: str):
    """FR-10: one row per expense category with limit/spent/remaining/%
    for the current month, ready for the UI to render directly."""
    month = _current_month()
    budgets = _budgets.get(user_email, {})
    categories = sorted(set(get_categories("expense")) | set(budgets.keys()))

    statuses = []
    for cat in categories:
        limit = budgets.get(cat)
        spent = get_category_spent(user_email, cat, month)
        remaining = round(limit - spent, 2) if limit else None
        percent = round((spent / limit) * 100, 1) if limit else None
        statuses.append({
            "category": cat, "limit": limit, "spent": spent,
            "remaining": remaining, "percent": percent,
            "over_budget": bool(limit and spent > limit),
            "suggested": suggest_budget(user_email, cat) if not limit else None,
        })
    return statuses


def get_budget_alerts(user_email: str):
    """FR-9: categories currently over their monthly budget."""
    return [s for s in get_budget_status(user_email) if s["over_budget"]]

