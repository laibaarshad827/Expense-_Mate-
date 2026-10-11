# ExpenseMate — Personal Expense Manager

A desktop personal finance application built with Python and CustomTkinter, backed by a local SQLite database. Built as a Software Construction course project covering the full Requirements → Design → Construction → Testing → Maintenance lifecycle.

## Features

- **Authentication**: registration with OTP verification, login/logout, forgot/reset password, update password, update email
- **Transactions & Categories**: add, edit, delete, and filter income/expense transactions; default and custom categories
- **Budgets**: monthly category budgets, over-budget alerts, and 3-month spending-based budget suggestions
- **Savings Goals**: create goals with optional deadlines, contribute toward them, track progress
- **Dashboard**: income, expense, and net savings summary
- **Reports**: filterable transaction table and category-wise spending breakdown
- **CSV Import/Export**: export all transactions to CSV; import from CSV with per-row validation (invalid rows are skipped and reported instead of failing the whole import)
- **Light/Dark Theme**: follows the operating system's appearance setting by default, with a manual toggle

## Tech Stack

- **Language:** Python
- **UI:** CustomTkinter
- **Database:** SQLite (local, no server needed)
- **Security:** bcrypt password hashing
- **Testing:** Python `unittest`; `radon` for cyclomatic complexity

## Project Structure

```
Expense-_Mate-/
├── app.py                    # Entry point and screen navigation controller
├── theme.py                  # Colors, fonts, sizes (light/dark pairs)
├── widgets.py                # Shared reusable UI components
├── backend_interface.py      # Single import surface the screens call into
├── database/
│   └── database.py           # Schema creation and connection setup
├── backend/
│   ├── models/               # Data classes
│   ├── repositories/         # SQL queries only, one repository per entity
│   └── services/             # Business logic and validation
│       ├── auth_service.py
│       ├── transaction_service.py
│       ├── budget_service.py
│       ├── savings_service.py
│       └── report_service.py
├── screens/                  # One CustomTkinter screen per file
├── tests/                    # Unit tests, one file per service module
├── assets/                   # Logo and static assets
├── requirements.txt
└── .gitignore
```

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database tables
python -m database.database

# 4. Run the app
python app.py
```

## Notes

- **OTP delivery:** there is no email server. When an OTP is generated, it is printed to the terminal where the app is running.
- **Database file:** `expense_mate.db` is created in the project root and is excluded from Git.

## Running Tests

```bash
python -m unittest discover tests -v
```

119 automated unit tests across five modules (Auth, Transactions/Categories, Budgets, Savings, CSV/Reports).

> **Warning:** the test suite creates and deletes `expense_mate.db` in the project root. Back up the file first if it holds data you want to keep.

## Architecture

Layered client-server (local):

```
Screens  →  Services  →  Repositories  →  SQLite
```

The UI never queries the database directly. All business rules and validation live in the service layer, and all SQL is isolated in the repository layer. Screens communicate with the backend through `backend_interface.py`, and every service function returns a `(success, message, data)` tuple.

## Team

| Member | Role |
|---|---|
| Laiba Arshad (Team Lead) | Backend: database, services, repositories, business logic, backend testing |
| Aiman Arshad | Frontend: CustomTkinter UI, UI/UX, frontend integration, frontend testing |

## Documentation

The SRS, Architecture Diagrams, Test Cases & Results, Metrics Report, Change Log, and Final Report are included in the course submission bundle.
