from typing import Optional
from database.database import get_connection


class BudgetRepository:

    def upsert_budget(self, user_id: int, category: str, limit_amount: float) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO BUDGET (user_id, category, limit_amount)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, category)
            DO UPDATE SET limit_amount = excluded.limit_amount, updated_at = datetime('now')
            """,
            (user_id, category, limit_amount),
        )
        conn.commit()
        conn.close()

    def get_budget(self, user_id: int, category: str) -> Optional[float]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT limit_amount FROM BUDGET WHERE user_id = ? AND category = ?",
            (user_id, category),
        )
        row = cursor.fetchone()
        conn.close()
        return row["limit_amount"] if row else None

    def get_all_budgets(self, user_id: int) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category, limit_amount FROM BUDGET WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return {row["category"]: row["limit_amount"] for row in rows}

    def get_category_spent(self, user_id: int, category: str, month: str) -> float:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM "TRANSACTION"
            WHERE user_id = ? AND type = 'expense' AND category = ?
              AND substr(transaction_date, 1, 7) = ?
            """,
            (user_id, category, month),
        )
        row = cursor.fetchone()
        conn.close()
        return row["total"]

    def get_monthly_spending_history(self, user_id: int, category: str) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT substr(transaction_date, 1, 7) as month, SUM(amount) as total
            FROM "TRANSACTION"
            WHERE user_id = ? AND type = 'expense' AND category = ?
            GROUP BY month
            """,
            (user_id, category),
        )
        rows = cursor.fetchall()
        conn.close()
        return {row["month"]: row["total"] for row in rows}

    def get_spent_by_category(self, user_id: int, month: str) -> dict:
        """{category: total expense} for one month - one query for all categories."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM "TRANSACTION"
            WHERE user_id = ? AND type = 'expense' AND substr(transaction_date, 1, 7) = ?
            GROUP BY category
            """,
            (user_id, month),
        )
        rows = cursor.fetchall()
        conn.close()
        return {row["category"]: row["total"] for row in rows}

    def get_spending_history_by_category(self, user_id: int) -> dict:
        """{category: {month: total expense}} - one query instead of one per category."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT category, substr(transaction_date, 1, 7) AS month, SUM(amount) AS total
            FROM "TRANSACTION"
            WHERE user_id = ? AND type = 'expense'
            GROUP BY category, month
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        history = {}
        for row in rows:
            history.setdefault(row["category"], {})[row["month"]] = row["total"]
        return history