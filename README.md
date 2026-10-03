# ExpenseMate — Personal Expense Manager

A desktop personal finance application built with Python and CustomTkinter, backed by a local SQLite database. Built as a Software Construction course project applying the full Requirements → Design → Construction → Testing → Maintenance lifecycle.

## Features

- **Authentication** — registration with OTP email verification, login/logout, forgot/reset password, update password, update email
- **Transactions & Categories** — add, edit, delete, and filter income/expense transactions; default and custom categories
- **Budgets** — set monthly category budgets, over-budget alerts, 3-month spending-based budget suggestions
- **Savings Goals** — create goals with optional deadlines, contribute toward them, track progress
- **Dashboard** — income, expense, and net savings summary at a glance
- **Reports** — filterable transaction table, category-wise spending breakdown
- **CSV Import/Export** — export all transactions to CSV; import from CSV with per-row validation (bad rows are skipped and reported, not fatal)
- **Multi-currency** — enter transactions in PKR, USD, EUR, GBP, AED, or SAR; automatically converted to PKR (the app's base currency) for all totals and budgets
- **Light/Dark theme** — adapts to the OS appearance setting by default, with a manual toggle

## Tech Stack

- **Language:** Python
- **UI:** CustomTkinter
- **Database:** SQLite (local, no server required)
- **Testing:** Python `unittest`, with `radon` for complexity analysis

## Project Structure

```
Expense-_Mate-/
├── app.py                      # Entry point — screen navigation controller
├── theme.py                    # Centralized colors, fonts, sizes (light/dark pairs)
├── widgets.py                  # Shared, reusable UI components
├── backend_interface.py        # Single import surface the frontend calls into
├── database/
│   └── database.py             # Schema creation, connection setup, migrations
├── backend/
│   ├── models/                 # Data classes (User, Otp)
│   ├── repositories/           # Raw SQL — one repository per entity
│   └── services/                # Business logic & validation
│       ├── auth_service.py
│       ├── transaction_service.py
│       ├── budget_service.py
│       ├── savings_service.py
│       ├── report_service.py
│       └── currency_service.py
├── screens/                     # One CustomTkinter screen per file
├── tests/                       # Unit tests (one file per service module)
├── assets/                      # Logo and static assets
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

# 3. Initialize the database
python -m database.database

# 4. Run the app
python app.py
```

## Running Tests

```bash
# Run everything
python -m unittest discover tests -v

# Run one module
python -m unittest tests.test_auth_service -v
```

119 automated unit tests across 5 modules (Auth, Transactions/Categories, Budgets, Savings, CSV/Reports), all passing.

## Architecture

Layered client-server (local):

```
UI (screens/)  →  Services (backend/services/)  →  Repositories (backend/repositories/)  →  SQLite
```

The UI never queries the database directly — all business logic and validation live in the service layer, and all SQL is isolated in the repository layer.

## Documentation

Full project documentation (SRS, Architecture Diagrams, Test Cases & Results, Metrics Report, Change Log, Final Report) is included in the course submission bundle.
