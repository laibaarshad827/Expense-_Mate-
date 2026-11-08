"""
Unit tests for TransactionService using in-memory fake repositories.
No database, no SQL - this is only possible because the service receives its
repositories through the constructor and never touches SQLite itself.
"""
import unittest
from types import SimpleNamespace

from backend.errors import ServiceError
from backend.models.transaction import Transaction
from backend.services.transaction_service import TransactionService


class FakeUsers:
    def get_by_email(self, email):
        return SimpleNamespace(user_id=1) if email == "ana@x.com" else None


class FakeCategories:
    def __init__(self):
        self.names = {("Food", "expense")}
    def get_categories(self, t): return [n for n, tt in self.names if tt == t]
    def category_exists(self, n, t): return (n, t) in self.names
    def add_category(self, n, t): self.names.add((n, t))


class FakeTransactions:
    def __init__(self):
        self.rows, self.next_id = {}, 1
    def create_transaction(self, uid, t, amount, cat, d, note, *extra):
        tid = self.next_id; self.next_id += 1
        self.rows[tid] = Transaction(tid, uid, t, amount, cat, d, note)
        return tid
    def get_by_id(self, uid, tid):
        r = self.rows.get(tid); return r if r and r.user_id == uid else None
    def get_transactions(self, uid, t=None, c=None):
        return [r for r in self.rows.values() if r.user_id == uid and (not t or r.type == t) and (not c or r.category == c)]
    def update_transaction(self, tid, amount, cat, d, note):
        r = self.rows[tid]; r.amount, r.category, r.transaction_date, r.note = amount, cat, d, note
    def delete_transaction(self, uid, tid):
        return self.rows.pop(tid, None) is not None
    def get_totals(self, uid):
        inc = sum(r.amount for r in self.rows.values() if r.type == "income")
        exp = sum(r.amount for r in self.rows.values() if r.type == "expense")
        return {"total_income": inc, "total_expense": exp, "transaction_count": len(self.rows)}


class TestTransactionService(unittest.TestCase):
    def setUp(self):
        self.s = TransactionService(FakeUsers(), FakeCategories(), FakeTransactions())

    def test_add_returns_record_in_screen_shape(self):
        rec = self.s.add_transaction("ana@x.com", "expense", 12.5, "Food", "2026-01-01", "n")
        self.assertEqual(rec, {"id": 1, "type": "expense", "amount": 12.5, "category": "Food",
                               "date": "2026-01-01", "note": "n"})

    def test_add_for_unknown_user_raises_business_error(self):
        with self.assertRaises(ServiceError) as ctx:
            self.s.add_transaction("ghost@x.com", "expense", 1, "Food", "2026-01-01", "")
        self.assertEqual(str(ctx.exception), "User not found.")

    def test_get_transactions_for_unknown_user_is_empty(self):
        self.assertEqual(self.s.get_transactions("ghost@x.com"), [])

    def test_update_missing_transaction_raises(self):
        with self.assertRaises(ServiceError):
            self.s.update_transaction("ana@x.com", 99, 1, "Food", "2026-01-01", "")

    def test_update_changes_the_record(self):
        self.s.add_transaction("ana@x.com", "expense", 1, "Food", "2026-01-01", "")
        rec = self.s.update_transaction("ana@x.com", 1, 7, "Food", "2026-02-02", "x")
        self.assertEqual((rec["amount"], rec["date"], rec["note"]), (7, "2026-02-02", "x"))

    def test_delete_twice_second_time_raises(self):
        self.s.add_transaction("ana@x.com", "expense", 1, "Food", "2026-01-01", "")
        self.s.delete_transaction("ana@x.com", 1)
        with self.assertRaises(ServiceError):
            self.s.delete_transaction("ana@x.com", 1)

    def test_duplicate_category_raises(self):
        with self.assertRaises(ServiceError):
            self.s.add_category("Food", "expense")

    def test_dashboard_net_savings_is_income_minus_expense(self):
        self.s.add_transaction("ana@x.com", "income", 1000, "Salary", "2026-01-01", "")
        self.s.add_transaction("ana@x.com", "expense", 250.25, "Food", "2026-01-02", "")
        d = self.s.dashboard_summary("ana@x.com")
        self.assertEqual((d["total_income"], d["total_expense"], d["net_savings"], d["transaction_count"]),
                         (1000, 250.25, 749.75, 2))


if __name__ == "__main__":
    unittest.main()