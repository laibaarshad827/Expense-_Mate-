"""
Report controller: routes the report actions to report_service and builds the
(success, message, data) response for the CSV import.
"""

from backend.controllers.common import fail
from backend.errors import ServiceError
from backend.services import report_service as _reports

export_transactions_csv = _reports.export_transactions_csv
get_report_transactions = _reports.get_report_transactions
get_category_breakdown = _reports.get_category_breakdown


def import_transactions_csv(user_email, file_path):
    try:
        result = _reports.csv_importer.import_file(user_email, file_path)
    except ServiceError as error:
        return fail(str(error))

    message = f"Imported {result.imported} of {result.total} rows."
    if result.skipped:
        message += f" {result.skipped} skipped."
    success = result.imported > 0 or not result.errors
    return success, message, {"imported": result.imported, "skipped": result.skipped, "errors": result.errors}