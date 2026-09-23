from typing import Optional, List
from database.database import get_connection


class CategoryRepository:

    def get_categories(self, txn_type: str) -> List[str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM CATEGORY WHERE type = ? ORDER BY is_default DESC, category_id ASC",
            (txn_type,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [row["name"] for row in rows]

    def category_exists(self, name: str, txn_type: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM CATEGORY WHERE LOWER(name) = LOWER(?) AND type = ?",
            (name, txn_type),
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def add_category(self, name: str, txn_type: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO CATEGORY (name, type, is_default) VALUES (?, ?, 0)",
            (name, txn_type),
        )
        conn.commit()
        conn.close()


class TransactionRepository:

    def _to_mock_shape(self, row: dict) -> dict:
        """Remap DB column names to match the exact keys the frontend expects
        (id, type, amount, category, date, note) — matching backend_interface.py's mock."""
        return {
            "id": row["transaction_id"],
            "type": row["type"],
            "amount": row["amount"],
            "category": row["category"],
            "date": row["transaction_date"],
            "note": row["note"],
        }

    def create_transaction(self, user_id: int, txn_type: str, amount: float,
                            category: str, txn_date: str, note: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO "TRANSACTION" (user_id, type, amount, category, transaction_date, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, txn_type, amount, category, txn_date, note),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    def get_transactions(self, user_id: int, txn_type: Optional[str] = None,
                          category: Optional[str] = None) -> List[dict]:
        conn = get_connection()
        cursor = conn.cursor()
        query = 'SELECT * FROM "TRANSACTION" WHERE user_id = ?'
        params = [user_id]
        if txn_type and txn_type != "All":
            query += " AND type = ?"
            params.append(txn_type)
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY transaction_date DESC, transaction_id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [self._to_mock_shape(dict(row)) for row in rows]

    def get_by_id(self, user_id: int, txn_id: int) -> Optional[dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM "TRANSACTION" WHERE user_id = ? AND transaction_id = ?',
            (user_id, txn_id),
        )
        row = cursor.fetchone()
        conn.close()
        return self._to_mock_shape(dict(row)) if row else None

    def update_transaction(self, txn_id: int, amount: float, category: str,
                            txn_date: str, note: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE "TRANSACTION"
            SET amount = ?, category = ?, transaction_date = ?, note = ?
            WHERE transaction_id = ?
            """,
            (amount, category, txn_date, note, txn_id),
        )
        conn.commit()
        conn.close()

    def delete_transaction(self, user_id: int, txn_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM "TRANSACTION" WHERE user_id = ? AND transaction_id = ?',
            (user_id, txn_id),
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def get_totals(self, user_id: int) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT type, COALESCE(SUM(amount), 0) as total FROM "TRANSACTION" WHERE user_id = ? GROUP BY type',
            (user_id,),
        )
        totals = {"income": 0.0, "expense": 0.0}
        for row in cursor.fetchall():
            totals[row["type"]] = row["total"]
        cursor.execute('SELECT COUNT(*) as cnt FROM "TRANSACTION" WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()["cnt"]
        conn.close()
        return {"total_income": totals["income"], "total_expense": totals["expense"], "transaction_count": count}