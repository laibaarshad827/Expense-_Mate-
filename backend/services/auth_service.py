"""
Auth business logic: registration, login, OTP generation/verification,
forgot/update password, update email.

Function names, parameters, and return format match the frontend's
contract file (backend_interface.py) exactly:
    (success: bool, message: str, data: dict | None)
"""

import re
import random
import bcrypt
from datetime import datetime, timedelta

from backend.repositories.user_repository import UserRepository, OtpRepository

OTP_LENGTH = 6
OTP_VALIDITY_MINUTES = 10

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_user_repo = UserRepository()
_otp_repo = OtpRepository()

# Very simple "session" - mirrors the mock's _current_user dict
_current_user = {}


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email or ""))


def is_valid_password(password: str) -> bool:
    return bool(password) and len(password) >= 6


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _generate_otp_code() -> str:
    return f"{random.randint(100000, 999999)}"


# ---------------------------------------------------------------------------
# FR-1 / FR-2: Account creation, login, logout
# ---------------------------------------------------------------------------

def register_user(username: str, email: str, password: str, confirm_password: str):
    if not username or not username.strip():
        return False, "Username cannot be empty.", None
    if not is_valid_email(email):
        return False, "Please enter a valid email address.", None
    if not is_valid_password(password):
        return False, "Password must be at least 6 characters long.", None
    if password != confirm_password:
        return False, "Passwords do not match.", None
    if _user_repo.get_by_email(email):
        return False, "An account with this email already exists.", None

    password_hash = _hash_password(password)
    user_id = _user_repo.create_user(username.strip(), email, password_hash)

    send_otp(email)
    return True, "Account created. Please verify the OTP sent to your email.", {"email": email}


def send_otp(email: str):
    user = _user_repo.get_by_email(email)
    if user is None:
        return False, "No account found with this email.", None

    otp_code = _generate_otp_code()
    expires_at = (datetime.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)).isoformat()
    _otp_repo.create_otp(user.user_id, otp_code, "GENERAL", expires_at)

    # In the real deployed app this would actually email the OTP.
    print(f"[MOCK OTP] OTP for {email} is: {otp_code}")
    return True, "OTP sent successfully. Check console (mock mode).", None


def verify_otp(email: str, otp_code: str):
    if not otp_code or not otp_code.strip():
        return False, "Please enter the OTP.", None

    user = _user_repo.get_by_email(email)
    if user is None:
        return False, "No account found with this email.", None

    otp = _otp_repo.get_latest_otp(user.user_id, "GENERAL")
    if otp is None:
        return False, "No OTP was requested for this email.", None
    if otp.is_used:
        return False, "This OTP has already been used.", None
    if datetime.fromisoformat(otp.expires_at) < datetime.now():
        return False, "This OTP has expired. Please request a new one.", None
    if otp.otp_code != otp_code.strip():
        return False, "Incorrect OTP. Please try again.", None

    _otp_repo.mark_used(otp.otp_id)
    _user_repo.set_verified(user.user_id)
    return True, "OTP verified successfully.", None


def login_user(email: str, password: str):
    if not is_valid_email(email):
        return False, "Please enter a valid email address.", None

    user = _user_repo.get_by_email(email)
    if user is None:
        return False, "No account found with this email.", None

    if not _verify_password(password, user.password_hash):
        return False, "Incorrect password.", None

    _current_user["email"] = email
    return True, "Login successful.", {"username": user.full_name, "email": email}


def logout_user():
    _current_user.clear()
    return True, "Logged out successfully.", None


# ---------------------------------------------------------------------------
# Forgot / Reset password
# ---------------------------------------------------------------------------

def request_password_reset(email: str):
    if _user_repo.get_by_email(email) is None:
        return False, "No account found with this email.", None
    return send_otp(email)


def reset_password(email: str, otp_code: str, new_password: str, confirm_password: str):
    ok, msg, _ = verify_otp(email, otp_code)
    if not ok:
        return False, msg, None

    if not is_valid_password(new_password):
        return False, "Password must be at least 6 characters long.", None
    if new_password != confirm_password:
        return False, "Passwords do not match.", None

    user = _user_repo.get_by_email(email)
    _user_repo.update_password(user.user_id, _hash_password(new_password))
    return True, "Password reset successfully. You can now log in.", None


# ---------------------------------------------------------------------------
# Update password / update email (while logged in)
# ---------------------------------------------------------------------------

def update_password(email: str, old_password: str, new_password: str, confirm_password: str):
    user = _user_repo.get_by_email(email)
    if user is None:
        return False, "User not found.", None

    if not _verify_password(old_password, user.password_hash):
        return False, "Current password is incorrect.", None

    if not is_valid_password(new_password):
        return False, "New password must be at least 6 characters long.", None
    if new_password != confirm_password:
        return False, "New passwords do not match.", None

    _user_repo.update_password(user.user_id, _hash_password(new_password))
    return True, "Password updated successfully.", None


def update_email(old_email: str, new_email: str, otp_code: str):
    if not is_valid_email(new_email):
        return False, "Please enter a valid new email address.", None
    if _user_repo.get_by_email(new_email):
        return False, "This email is already in use.", None

    ok, msg, _ = verify_otp(old_email, otp_code)
    if not ok:
        return False, msg, None

    user = _user_repo.get_by_email(old_email)
    _user_repo.update_email(user.user_id, new_email)
    return True, "Email updated successfully.", {"email": new_email}