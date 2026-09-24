from typing import Optional, List
from database.database import get_connection


class SavingsRepository:

    def create_goal(self, user_id: int, goal_name: str, target_amount: float, deadline: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO SAVINGS_GOAL (user_id, goal_name, target_amount, current_amount, deadline)
            VALUES (?, ?, ?, 0, ?)
            """,
            (user_id, goal_name, target_amount, deadline),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    def get_all_goals(self, user_id: int) -> List[dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM SAVINGS_GOAL WHERE user_id = ? ORDER BY goal_id DESC",
            (user_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_by_id(self, user_id: int, goal_id: int) -> Optional[dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM SAVINGS_GOAL WHERE user_id = ? AND goal_id = ?",
            (user_id, goal_id),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_goal(self, goal_id: int, goal_name: str, target_amount: float, deadline: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE SAVINGS_GOAL
            SET goal_name = ?, target_amount = ?, deadline = ?
            WHERE goal_id = ?
            """,
            (goal_name, target_amount, deadline, goal_id),
        )
        conn.commit()
        conn.close()

    def delete_goal(self, user_id: int, goal_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM SAVINGS_GOAL WHERE user_id = ? AND goal_id = ?",
            (user_id, goal_id),
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def add_contribution(self, goal_id: int, amount: float) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE SAVINGS_GOAL SET current_amount = current_amount + ? WHERE goal_id = ?",
            (amount, goal_id),
        )
        conn.commit()
        conn.close()

    def get_totals(self, user_id: int) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COALESCE(SUM(target_amount), 0) as total_target,
                   COALESCE(SUM(current_amount), 0) as total_saved,
                   COUNT(*) as goal_count
            FROM SAVINGS_GOAL WHERE user_id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row)