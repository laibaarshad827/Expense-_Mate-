"""
CsvImporter - imports transactions from a CSV file (REWRITTEN in Assignment 02, Part C).

Old design (import_transactions_csv in report_service): ONE function of about 60
lines, cyclomatic complexity 21 (grade D). It opened the file, parsed the CSV,
checked the columns, cleaned and validated every field, saved the rows,
counted results and built the response message, all interleaved. A small
helper extraction is not enough to fix that, because the stages share state
and the response formatting is woven through them.

New design: a class where each stage is its own small method, and the
transaction service and user repository are injected (so it can be tested
without a database). It returns an ImportResult; the controller turns that
into the (success, message, data) response.
"""

import csv
from dataclasses import dataclass, field
from typing import List

from backend.errors import ServiceError
from backend.validators import is_valid_amount, is_valid_date

REQUIRED_COLUMNS = ("type", "category", "amount", "date")
FIRST_DATA_ROW_NUMBER = 2      # row 1 is the header


@dataclass
class ImportResult:
    total: int
    imported: int
    errors: List[str] = field(default_factory=list)

    @property
    def skipped(self) -> int:
        return self.total - self.imported


class CsvImporter:

    def __init__(self, transaction_service, user_repo):
        self._transactions = transaction_service
        self._users = user_repo

    # ---- public ----
    def import_file(self, user_email: str, file_path: str) -> ImportResult:
        if self._users.get_by_email(user_email) is None:
            raise ServiceError("User not found.")

        rows, columns = self._read(file_path)
        self._check_not_empty(rows)
        self._check_columns(columns)

        result = ImportResult(total=len(rows), imported=0)
        for number, row in enumerate(rows, start=FIRST_DATA_ROW_NUMBER):
            self._import_row(user_email, number, row, result)
        return result

    # ---- stage 1: read ----
    @staticmethod
    def _read(file_path):
        try:
            with open(file_path, newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                return list(reader), reader.fieldnames or []
        except OSError as error:
            raise ServiceError(f"Could not read file: {error}")
        except csv.Error as error:
            raise ServiceError(f"Invalid CSV file: {error}")

    # ---- stage 2: file-level checks ----
    @staticmethod
    def _check_not_empty(rows):
        if not rows:
            raise ServiceError("CSV file is empty.")

    @staticmethod
    def _check_columns(columns):
        missing = [name for name in REQUIRED_COLUMNS if name not in columns]
        if missing:
            raise ServiceError(f"CSV is missing required column(s): {', '.join(missing)}.")

    # ---- stage 3: one row ----
    @staticmethod
    def _parse_row(row, number):
        """Returns (fields, None) for a good row or (None, error_message) for a bad one."""
        txn_type = (row.get("type") or "").strip().lower()
        category = (row.get("category") or "").strip()
        amount = row.get("amount")
        date_text = (row.get("date") or "").strip()

        if txn_type not in ("income", "expense"):
            return None, f"Row {number}: invalid type '{txn_type}' (must be income or expense)."
        amount_ok, clean_amount = is_valid_amount(amount)
        if not amount_ok:
            return None, f"Row {number}: invalid amount '{amount}'."
        if not category:
            return None, f"Row {number}: missing category."
        if not is_valid_date(date_text):
            return None, f"Row {number}: invalid date '{date_text}' (expected YYYY-MM-DD)."

        fields = (txn_type, clean_amount, category, date_text, (row.get("note") or "").strip())
        return fields, None

    def _import_row(self, user_email, number, row, result):
        fields, problem = self._parse_row(row, number)
        if problem:
            result.errors.append(problem)
            return
        txn_type, amount, category, date_text, note = fields
        try:
            self._transactions.add_transaction(user_email, txn_type, amount, category, date_text, note)
            result.imported += 1
        except ServiceError as error:
            result.errors.append(f"Row {number}: {error}")