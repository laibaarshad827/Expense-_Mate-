"""
AuthService - authentication business rules (REWRITTEN in Assignment 02, Part C).

Old design problems (the module this class replaces):
  * module-level singletons (_user_repo, _otp_repo) and a global _current_user dict
  * side effects hard-wired inside the rules: print() for OTP delivery,
    datetime.now() for expiry, random for OTP codes, bcrypt for hashing
    -> impossible to unit-test OTP expiry, or anything else, without a real
       database, real bcrypt (slow) and real time
  * input validation, business rules and (success, message, data) formatting
    all mixed in every function
  * reset_password consumed the OTP BEFORE checking the new password, so one
    typo burned the code and forced the user to start over

New design: every collaborator is injected, the class only applies business
rules, and it raises ServiceError (the controller formats the response).
"""

import secrets
from datetime import datetime, timedelta

import bcrypt

from backend.errors import ServiceError
from expensemate_config import OTP_LENGTH, OTP_VALIDITY_MINUTES

OTP_PURPOSE = "GENERAL"   # one purpose for all flows - see the report for why this was kept


class PasswordHasher:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


class OtpGenerator:
    """Cryptographically secure numeric codes (secrets, not random)."""

    def __init__(self, length: int = OTP_LENGTH):
        self.length = length

    def generate(self) -> str:
        lowest = 10 ** (self.length - 1)
        return str(lowest + secrets.randbelow(9 * lowest))


def console_delivery(email: str, code: str) -> None:
    """Default 'delivery': print to the terminal (there is no mail server)."""
    print(f"[MOCK OTP] OTP for {email} is: {code}")


class AuthService:

    def __init__(self, user_repo, otp_repo, hasher=None, otp_generator=None,
                 deliver_otp=console_delivery, clock=datetime.now,
                 otp_validity_minutes: int = OTP_VALIDITY_MINUTES):
        self._users = user_repo
        self._otps = otp_repo
        self._hasher = hasher or PasswordHasher()
        self._otp_generator = otp_generator or OtpGenerator()
        self._deliver_otp = deliver_otp
        self._clock = clock
        self._otp_validity = timedelta(minutes=otp_validity_minutes)
        self._current_email = None

    @property
    def current_email(self):
        return self._current_email

    # ---- helpers ----
    def _require_user(self, email):
        user = self._users.get_by_email(email)
        if user is None:
            raise ServiceError("No account found with this email.")
        return user

    def _consume_otp(self, email, code):
        """Checks the latest OTP for this user and marks it used. Returns the user."""
        user = self._require_user(email)
        otp = self._otps.get_latest_otp(user.user_id, OTP_PURPOSE)
        if otp is None:
            raise ServiceError("No OTP was requested for this email.")
        if otp.is_used:
            raise ServiceError("This OTP has already been used.")
        if datetime.fromisoformat(otp.expires_at) < self._clock():
            raise ServiceError("This OTP has expired. Please request a new one.")
        if otp.otp_code != code:
            raise ServiceError("Incorrect OTP. Please try again.")
        self._otps.mark_used(otp.otp_id)
        self._users.set_verified(user.user_id)
        return user

    # ---- registration & OTP ----
    def register(self, username, email, password):
        if self._users.get_by_email(email):
            raise ServiceError("An account with this email already exists.")
        self._users.create_user(username, email, self._hasher.hash(password))
        self.send_otp(email)
        return {"email": email}

    def send_otp(self, email):
        user = self._require_user(email)
        code = self._otp_generator.generate()
        expires_at = (self._clock() + self._otp_validity).isoformat()
        self._otps.create_otp(user.user_id, code, OTP_PURPOSE, expires_at)
        self._deliver_otp(email, code)

    def verify_otp(self, email, code):
        self._consume_otp(email, code)

    # ---- login / logout ----
    def login(self, email, password):
        user = self._require_user(email)
        if not self._hasher.verify(password, user.password_hash):
            raise ServiceError("Incorrect password.")
        self._current_email = email
        return {"username": user.full_name, "email": email}

    def logout(self):
        self._current_email = None

    # ---- passwords ----
    def request_password_reset(self, email):
        self.send_otp(email)

    def reset_password(self, email, code, new_password):
        user = self._consume_otp(email, code)
        self._users.update_password(user.user_id, self._hasher.hash(new_password))

    def update_password(self, email, old_password, new_password):
        user = self._users.get_by_email(email)
        if user is None:
            raise ServiceError("User not found.")
        if not self._hasher.verify(old_password, user.password_hash):
            raise ServiceError("Current password is incorrect.")
        self._users.update_password(user.user_id, self._hasher.hash(new_password))

    # ---- email ----
    def update_email(self, old_email, new_email, code):
        if self._users.get_by_email(new_email):
            raise ServiceError("This email is already in use.")
        user = self._consume_otp(old_email, code)
        self._users.update_email(user.user_id, new_email)
        return {"email": new_email}