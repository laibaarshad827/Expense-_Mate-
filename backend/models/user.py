"""
Data classes representing rows from the USER and OTP tables.
"""

from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    full_name: str
    email: str
    password_hash: str
    is_verified: bool
    created_at: str

    @staticmethod
    def from_row(row) -> "User":
        return User(
            user_id=row["user_id"],
            full_name=row["full_name"],
            email=row["email"],
            password_hash=row["password_hash"],
            is_verified=bool(row["is_verified"]),
            created_at=row["created_at"],
        )


@dataclass
class Otp:
    otp_id: int
    user_id: int
    otp_code: str
    purpose: str
    expires_at: str
    is_used: bool
    created_at: str

    @staticmethod
    def from_row(row) -> "Otp":
        return Otp(
            otp_id=row["otp_id"],
            user_id=row["user_id"],
            otp_code=row["otp_code"],
            purpose=row["purpose"],
            expires_at=row["expires_at"],
            is_used=bool(row["is_used"]),
            created_at=row["created_at"],
        )