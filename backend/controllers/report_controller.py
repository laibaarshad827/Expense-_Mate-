# backend/controllers/report_controller.py
"""Report controller (thin for now). The CSV import becomes a CsvImporter class in Part C."""
from backend.services import report_service as _reports

export_transactions_csv = _reports.export_transactions_csv
import_transactions_csv = _reports.import_transactions_csv
get_report_transactions = _reports.get_report_transactions
get_category_breakdown = _reports.get_category_breakdown