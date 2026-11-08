"""
Unit tests for the rewritten CsvImporter (and the report controller's response
building). The transaction service is a fake and the CSV files are temporary,
so there is no database.
"""
import os
import tempfile
import unittest
from types import SimpleNamespace

from backend.controllers import report_controller as rc
from backend.errors import ServiceError
from backend.services.csv_importer import CsvImporter, ImportResult


class FakeUsers:
    def get_by_email(self, email): return SimpleNamespace(user_id=1) if email == "ana@x.com" else None


class FakeTransactions:
    def __init__(self): self.added = []
    def add_transaction(self, email, txn_type, amount, category, date_text, note):
        if category == "Boom":
            raise ServiceError("Simulated failure.")
        self.added.append((email, txn_type, amount, category, date_text, note))


class CsvCase(unittest.TestCase):
    def setUp(self):
        self.txns = FakeTransactions()
        self.importer = CsvImporter(self.txns, FakeUsers())
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def write(self, text, name="in.csv"):
        path = os.path.join(self.dir.name, name)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    def run_import(self, text, email="ana@x.com"):
        return self.importer.import_file(email, self.write(text))

    def message_of(self, text, email="ana@x.com"):
        with self.assertRaises(ServiceError) as ctx:
            self.run_import(text, email)
        return str(ctx.exception)


HEADER = "type,category,amount,date,note\n"


class TestImportRows(CsvCase):
    def test_valid_rows_are_imported_and_cleaned(self):
        result = self.run_import(HEADER + " INCOME ,Salary,5000.456,2026-09-01, pay \nexpense,Food,250,2026-09-02,\n")
        self.assertEqual((result.total, result.imported, result.skipped, result.errors), (2, 2, 0, []))
        self.assertEqual(self.txns.added[0], ("ana@x.com", "income", 5000.46, "Salary", "2026-09-01", "pay"))
        self.assertEqual(self.txns.added[1][5], "")

    def test_bad_rows_are_skipped_with_their_row_numbers(self):
        result = self.run_import(
            HEADER +
            "weird,Food,100,2026-09-01,\n"          # row 2
            "expense,Food,-5,2026-09-01,\n"         # row 3
            "expense,,5,2026-09-01,\n"              # row 4
            "expense,Food,5,01-09-2026,\n"          # row 5
            "expense,Food,9,2026-09-01,ok\n")       # row 6 (good)
        self.assertEqual((result.total, result.imported, result.skipped), (5, 1, 4))
        self.assertEqual(result.errors, [
            "Row 2: invalid type 'weird' (must be income or expense).",
            "Row 3: invalid amount '-5'.",
            "Row 4: missing category.",
            "Row 5: invalid date '01-09-2026' (expected YYYY-MM-DD).",
        ])

    def test_a_service_error_for_one_row_does_not_stop_the_import(self):
        result = self.run_import(HEADER + "expense,Boom,5,2026-09-01,\nexpense,Food,6,2026-09-01,\n")
        self.assertEqual((result.imported, result.skipped), (1, 1))
        self.assertEqual(result.errors, ["Row 2: Simulated failure."])

    def test_extra_columns_are_ignored_and_note_is_optional(self):
        result = self.run_import("type,category,amount,date,extra\nexpense,Food,5,2026-09-01,zzz\n")
        self.assertEqual(result.imported, 1)
        self.assertEqual(self.txns.added[0][5], "")


class TestFileLevelErrors(CsvCase):
    def test_unknown_user(self):
        self.assertEqual(self.message_of(HEADER + "expense,Food,5,2026-09-01,\n", "ghost@x.com"), "User not found.")

    def test_missing_file(self):
        with self.assertRaises(ServiceError) as ctx:
            self.importer.import_file("ana@x.com", os.path.join(self.dir.name, "nope.csv"))
        self.assertTrue(str(ctx.exception).startswith("Could not read file:"))

    def test_empty_file_and_header_only_file(self):
        self.assertEqual(self.message_of(""), "CSV file is empty.")
        self.assertEqual(self.message_of(HEADER), "CSV file is empty.")

    def test_missing_required_columns_are_named(self):
        self.assertEqual(self.message_of("category,amount,date\nFood,5,2026-09-01\n"),
                         "CSV is missing required column(s): type.")
        self.assertEqual(self.message_of("foo,bar\n1,2\n"),
                         "CSV is missing required column(s): type, category, amount, date.")


class TestImportResult(unittest.TestCase):
    def test_skipped_is_total_minus_imported(self):
        self.assertEqual(ImportResult(total=10, imported=7).skipped, 3)


class TestReportControllerResponse(CsvCase):
    def setUp(self):
        super().setUp()
        self.real = rc._reports.csv_importer
        rc._reports.csv_importer = self.importer
    def tearDown(self): rc._reports.csv_importer = self.real

    def respond(self, text): return rc.import_transactions_csv("ana@x.com", self.write(text))

    def test_all_good(self):
        ok, message, data = self.respond(HEADER + "expense,Food,5,2026-09-01,\n")
        self.assertEqual((ok, message, data), (True, "Imported 1 of 1 rows.",
                                                {"imported": 1, "skipped": 0, "errors": []}))

    def test_partly_good_is_still_a_success_with_a_skipped_count(self):
        ok, message, data = self.respond(HEADER + "expense,Food,5,2026-09-01,\nexpense,Food,-1,2026-09-01,\n")
        self.assertTrue(ok)
        self.assertEqual(message, "Imported 1 of 2 rows. 1 skipped.")
        self.assertEqual(len(data["errors"]), 1)

    def test_nothing_imported_because_every_row_is_bad_is_a_failure_with_details(self):
        ok, message, data = self.respond(HEADER + "expense,Food,-1,2026-09-01,\n")
        self.assertFalse(ok)
        self.assertEqual(message, "Imported 0 of 1 rows. 1 skipped.")
        self.assertEqual(data["imported"], 0)

    def test_file_level_error_becomes_a_failure_response(self):
        self.assertEqual(self.respond(""), (False, "CSV file is empty.", None))


if __name__ == "__main__":
    unittest.main()