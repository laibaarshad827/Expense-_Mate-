"""
Safety switch for the whole test package.

Several tests delete the database file in setUp/tearDown. Before the
configuration migration they used the SAME hard-coded file as the app
(expense_mate.db), so running the tests wiped the real data.

This runs before any test module is imported and points the tests at a
throw-away database in the system temp folder via EXPENSEMATE_DB.
Run tests from the project folder with:  python -m unittest discover -v
"""
import os
import tempfile

os.environ.setdefault(
    "EXPENSEMATE_DB", os.path.join(tempfile.gettempdir(), "expensemate_test.db")
)
