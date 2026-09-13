"""
Auth business logic: registration, login, OTP generation/verification,
forgot/update password, update email.
"""

import re
import random
import string
import bcrypt
from datetime import datetime, timedelta

from backend.repositories.user_repository import UserRepository, OtpRepository

OTP_LENGTH = 6
OTP_VALIDITY_MINUTES = 10

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    pass


class AuthService:

    def __init__(self):
        self.user_repo = UserRepository()
        self.otp_repo = OtpRepository()

    def _validate_email(self, email: str) -> None:
        if not email or not EMAIL_REGEX.match(email):
            raise AuthError("Please enter a valid email address.")

    def _validate_password(self, password: str) -> None:
        if not password or len(password) < 8:
            raise AuthError("Password must be at least 8 characters long.")
        if not any(c.isdigit() for c in password):
            raise AuthError("Password must contain at least one number.")
        if not any(c.isalpha() for c in password):
            raise AuthError("Password must contain at least one letter.")

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def _generate_otp_code(self) -> str:
        return "".join(random.choices(string.digits, k=OTP_LENGTH))

    def generate_otp(self, user_id: int, purpose: str) -> str:
        code = self._generate_otp_code()
        expires_at = (datetime.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)).isoformat()
        self.otp_repo.create_otp(user_id, code, purpose, expires_at)
        return code

    def verify_otp(self, user_id: int, purpose: str, code: str) -> None:
        otp = self.otp_repo.get_latest_otp(user_id, purpose)
        if not otp:
            raise AuthError("No OTP found. Please request a new one.")
        if otp.is_used:
            raise AuthError("This OTP has already been used.")
        if datetime.fromisoformat(otp.expires_at) < datetime.now():
            raise AuthError("This OTP has expired. Please request a new one.")
        if otp.otp_code != code:
            raise AuthError("Incorrect OTP. Please try again.")

        self.otp_repo.mark_used(otp.otp_id)

    def register(self, full_name: str, email: str, password: str) -> int:
        if not full_name or not full_name.strip():
            raise AuthError("Full name is required.")
        self._validate_email(email)
        self._validate_password(password)

        if self.user_repo.get_by_email(email):
            raise AuthError("An account with this email already exists.")

        password_hash = self._hash_password(password)
        user_id = self.user_repo.create_user(full_name.strip(), email, password_hash)

        self.generate_otp(user_id, purpose="REGISTER")
        return user_id

    def verify_registration_otp(self, user_id: int, code: str) -> None:
        self.verify_otp(user_id, purpose="REGISTER", code=code)
        self.user_repo.set_verified(user_id)

    def login(self, email: str, password: str):
        self._validate_email(email)

        user = self.user_repo.get_by_email(email)
        if not user:
            raise AuthError("No account found with this email.")

        if not self._verify_password(password, user.password_hash):
            raise AuthError("Incorrect password.")

        if not user.is_verified:
            raise AuthError("Please verify your account via OTP before logging in.")

        return user

    def request_password_reset(self, email: str) -> int:
        self._validate_email(email)
        user = self.user_repo.get_by_email(email)
        if not user:
            raise AuthError("No account found with this email.")

        self.generate_otp(user.user_id, purpose="RESET_PASSWORD")
        return user.user_id

    def reset_password(self, user_id: int, otp_code: str, new_password: str) -> None:
        self.verify_otp(user_id, purpose="RESET_PASSWORD", code=otp_code)
        self._validate_password(new_password)
        new_hash = self._hash_password(new_password)
        self.user_repo.update_password(user_id, new_hash)

    def update_password(self, user_id: int, current_password: str, new_password: str) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthError("User not found.")

        if not self._verify_password(current_password, user.password_hash):
            raise AuthError("Current password is incorrect.")

        self._validate_password(new_password)
        new_hash = self._hash_password(new_password)
        self.user_repo.update_password(user_id, new_hash)

    def update_email(self, user_id: int, new_email: str) -> None:
        self._validate_email(new_email)
        if self.user_repo.get_by_email(new_email):
            raise AuthError("This email is already in use.")
        self.user_repo.update_email(user_id, new_email)