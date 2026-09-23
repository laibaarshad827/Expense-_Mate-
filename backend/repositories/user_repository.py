"""
Repository layer for USER and OTP tables.
Only raw SQL queries live here - no business rules, no hashing logic.
"""

from typing import Optional
from database.database import get_connection
from backend.models.user import User, Otp


class UserRepository:

    def create_user(self, full_name: str, email: str, password_hash: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO USER (full_name, email, password_hash, is_verified)
            VALUES (?, ?, ?, 0)
            """,
            (full_name, email, password_hash),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    def get_by_email(self, email: str) -> Optional[User]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USER WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        return User.from_row(row) if row else None

    def get_by_id(self, user_id: int) -> Optional[User]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USER WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return User.from_row(row) if row else None

    def set_verified(self, user_id: int) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE USER SET is_verified = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def update_password(self, user_id: int, new_password_hash: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE USER SET password_hash = ? WHERE user_id = ?",
            (new_password_hash, user_id),
        )
        conn.commit()
        conn.close()

    def update_email(self, user_id: int, new_email: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE USER SET email = ? WHERE user_id = ?",
            (new_email, user_id),
        )
        conn.commit()
        conn.close()


class OtpRepository:

    def create_otp(self, user_id: int, otp_code: str, purpose: str, expires_at: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO OTP (user_id, otp_code, purpose, expires_at, is_used)
            VALUES (?, ?, ?, ?, 0)
            """,
            (user_id, otp_code, purpose, expires_at),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    def get_latest_otp(self, user_id: int, purpose: str) -> Optional[Otp]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
           "SELECT * FROM OTP WHERE user_id = ? AND purpose = ?" \
           " ORDER BY otp_id DESC LIMIT 1"
           , (user_id, purpose)
           )
        row = cursor.fetchone()
        conn.close()
        return Otp.from_row(row) if row else None

    def mark_used(self, otp_id: int) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE OTP SET is_used = 1 WHERE otp_id = ?", (otp_id,))
        conn.commit()
        conn.close()