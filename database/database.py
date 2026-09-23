"""
Database connection and schema setup for ExpenseMate.
Creates USER and OTP tables if they don't already exist.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "expense_mate.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS USER (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS OTP (
            otp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            otp_code TEXT NOT NULL,
            purpose TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_used INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES USER (user_id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
def add_day2_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CATEGORY (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            is_default INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(name, type)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "TRANSACTION" (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            amount REAL NOT NULL CHECK (amount > 0),
            category TEXT NOT NULL,
            transaction_date TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES USER (user_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("SELECT COUNT(*) as cnt FROM CATEGORY WHERE is_default = 1")
    if cursor.fetchone()["cnt"] == 0:
        defaults = [
            ("Salary", "income"), ("Freelance", "income"), ("Business", "income"),
            ("Gift", "income"), ("Other Income", "income"),
            ("Food", "expense"), ("Rent", "expense"), ("Transport", "expense"),
            ("Utilities", "expense"), ("Shopping", "expense"), ("Health", "expense"),
            ("Education", "expense"), ("Entertainment", "expense"), ("Other Expense", "expense"),
        ]
        cursor.executemany(
            "INSERT INTO CATEGORY (name, type, is_default) VALUES (?, ?, 1)", defaults
        )
    conn.commit()
    conn.close()
def add_day3_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS BUDGET (
            budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            limit_amount REAL NOT NULL CHECK (limit_amount > 0),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, category),
            FOREIGN KEY (user_id) REFERENCES USER (user_id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    add_day2_tables()
    add_day3_tables()
    print(f"Database initialized at {DB_PATH}")