"""
Behaviour snapshot of ExpenseMate's back end (read-only).

It works on a TEMPORARY COPY of expense_mate.db, so it can never change your data,
and prints the results of the main read operations plus the OTP / password rules.
Run it on the Assignment 01 code and on the migrated code, then compare the two
outputs: they must be identical.

    python tools/smoke_check.py
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

source_db = ROOT / "expense_mate.db"
if not source_db.exists():
    sys.exit("expense_mate.db not found in the project folder.")

tmp_dir = tempfile.mkdtemp()
tmp_db = os.path.join(tmp_dir, "smoke_copy.db")
shutil.copy(source_db, tmp_db)
os.environ["EXPENSEMATE_DB"] = tmp_db      # used by the migrated code; ignored by Assignment 01 code

# Assignment 01 code has the path hard-coded, so also make sure it reads the COPY:
import database.database as database_module  # noqa: E402
database_module.DB_PATH = Path(tmp_db)

from backend.services import auth_service, transaction_service, budget_service, savings_service, report_service  # noqa: E402

conn = sqlite3.connect(tmp_db)
email = conn.execute("SELECT email FROM USER ORDER BY user_id LIMIT 1").fetchone()[0]
conn.close()

result = {
    "categories_expense": transaction_service.get_categories("expense"),
    "transactions": transaction_service.get_transactions(email),
    "dashboard_summary": transaction_service.get_dashboard_summary(email),
    "budget_status": budget_service.get_budget_status(email),
    "budget_alerts": budget_service.get_budget_alerts(email),
    "savings_goals": savings_service.get_savings_goals(email),
    "savings_summary": savings_service.get_savings_summary(email),
    "category_breakdown": report_service.get_category_breakdown(email),
    "password_rule": {
        "5_chars_valid": auth_service.is_valid_password("12345"),
        "6_chars_valid": auth_service.is_valid_password("123456"),
        "register_short_password_message": auth_service.register_user("T", "t@example.com", "12345", "12345")[1],
    },
    "otp": {"length": len(auth_service._generate_otp_code()),
            "validity_minutes": auth_service.OTP_VALIDITY_MINUTES},
}
print(json.dumps(result, indent=2, sort_keys=True, default=str))
shutil.rmtree(tmp_dir, ignore_errors=True)
