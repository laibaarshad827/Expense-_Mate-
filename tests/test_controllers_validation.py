"""
Controller tests: basic input validation happens in the controller and the
service is NOT called when the input is bad. The service is replaced by a spy,
so no database is involved.
"""
import unittest

from backend.controllers import transaction_controller as tc
from backend.controllers import budget_controller as bc


class SpyService:
    def __init__(self): self.calls = []
    def __getattr__(self, name):
        def record(*a, **k): self.calls.append(name); return {"spy": True}
        return record


class TestTransactionControllerValidation(unittest.TestCase):
    def setUp(self):
        self.real, self.spy = tc._service, SpyService()
        tc._service = self.spy
    def tearDown(self): tc._service = self.real

    def test_bad_inputs_are_rejected_without_calling_the_service(self):
        bad = [("nope", "5", "Food", "2026-01-01", "Invalid transaction type."),
               ("expense", "-5", "Food", "2026-01-01", "Please enter a valid amount greater than 0."),
               ("expense", "abc", "Food", "2026-01-01", "Please enter a valid amount greater than 0."),
               ("expense", "5", "  ", "2026-01-01", "Please select a category."),
               ("expense", "5", "Food", "01-01-2026", "Please enter a valid date in YYYY-MM-DD format.")]
        for t, amount, cat, d, message in bad:
            with self.subTest(message=message, amount=amount):
                self.assertEqual(tc.add_transaction("a@x.com", t, amount, cat, d), (False, message, None))
        self.assertEqual(self.spy.calls, [])

    def test_valid_input_is_cleaned_then_delegated(self):
        ok, message, data = tc.add_transaction("a@x.com", "expense", "12.345", "Food", " 2026-01-01 ", " hi ")
        self.assertTrue(ok); self.assertEqual(message, "Transaction added successfully.")
        self.assertEqual(self.spy.calls, ["add_transaction"])

    def test_update_validates_before_delegating(self):
        self.assertFalse(tc.update_transaction("a@x.com", 1, "0", "Food", "2026-01-01")[0])
        self.assertEqual(self.spy.calls, [])

    def test_add_category_checks(self):
        self.assertEqual(tc.add_category("  ", "expense"), (False, "Category name cannot be empty.", None))
        self.assertEqual(tc.add_category("X", "bad"), (False, "Invalid category type.", None))
        self.assertEqual(self.spy.calls, [])


class TestBudgetControllerValidation(unittest.TestCase):
    def setUp(self):
        self.real, self.spy = bc._service, SpyService()
        bc._service = self.spy
    def tearDown(self): bc._service = self.real

    def test_invalid_limit_never_reaches_the_service(self):
        for bad in ("-100", "0", "abc", None):
            self.assertEqual(bc.set_budget("a@x.com", "Food", bad),
                             (False, "Please enter a valid budget amount greater than 0.", None))
        self.assertEqual(self.spy.calls, [])


if __name__ == "__main__":
    unittest.main()