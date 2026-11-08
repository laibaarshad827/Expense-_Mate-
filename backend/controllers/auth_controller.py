"""
Auth controller: validates the BASIC input (required fields, formats, password
rules), calls AuthService, and builds the (success, message, data) response.
No SQL here; the repositories are only used to build the service.
"""

from backend.controllers.common import ok, fail
from backend.errors import ServiceError
from backend.repositories.user_repository import OtpRepository, UserRepository
from backend.services.auth_service import AuthService
from backend.validators import is_valid_email, is_valid_password
from expensemate_config import MIN_PASSWORD_LENGTH

__all__ = [
    "register_user", "send_otp", "verify_otp", "login_user", "logout_user",
    "request_password_reset", "reset_password", "update_password", "update_email",
    "is_valid_email", "is_valid_password",
]

_service = AuthService(UserRepository(), OtpRepository())

_BAD_EMAIL = "Please enter a valid email address."
_NO_OTP = "Please enter the OTP."
_SHORT_PASSWORD = f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."


def _password_problem(password, confirm, short_message, mismatch_message):
    """Returns the first basic problem with a new password, or None."""
    if not is_valid_password(password):
        return short_message
    if password != confirm:
        return mismatch_message
    return None


def register_user(username, email, password, confirm_password):
    if not username or not username.strip():
        return fail("Username cannot be empty.")
    if not is_valid_email(email):
        return fail(_BAD_EMAIL)
    problem = _password_problem(password, confirm_password, _SHORT_PASSWORD, "Passwords do not match.")
    if problem:
        return fail(problem)
    try:
        data = _service.register(username.strip(), email, password)
        return ok("Account created. Please verify the OTP sent to your email.", data)
    except ServiceError as error:
        return fail(str(error))


def send_otp(email):
    try:
        _service.send_otp(email)
        return ok("OTP sent successfully. Check console (mock mode).")
    except ServiceError as error:
        return fail(str(error))


def verify_otp(email, otp_code):
    if not otp_code or not otp_code.strip():
        return fail(_NO_OTP)
    try:
        _service.verify_otp(email, otp_code.strip())
        return ok("OTP verified successfully.")
    except ServiceError as error:
        return fail(str(error))


def login_user(email, password):
    if not is_valid_email(email):
        return fail(_BAD_EMAIL)
    try:
        return ok("Login successful.", _service.login(email, password))
    except ServiceError as error:
        return fail(str(error))


def logout_user():
    _service.logout()
    return ok("Logged out successfully.")


def request_password_reset(email):
    try:
        _service.request_password_reset(email)
        return ok("OTP sent successfully. Check console (mock mode).")
    except ServiceError as error:
        return fail(str(error))


def reset_password(email, otp_code, new_password, confirm_password):
    if not otp_code or not otp_code.strip():
        return fail(_NO_OTP)
    # Checked BEFORE the OTP is consumed, so a typo no longer burns the code.
    problem = _password_problem(new_password, confirm_password, _SHORT_PASSWORD, "Passwords do not match.")
    if problem:
        return fail(problem)
    try:
        _service.reset_password(email, otp_code.strip(), new_password)
        return ok("Password reset successfully. You can now log in.")
    except ServiceError as error:
        return fail(str(error))


def update_password(email, old_password, new_password, confirm_password):
    problem = _password_problem(
        new_password, confirm_password,
        f"New password must be at least {MIN_PASSWORD_LENGTH} characters long.",
        "New passwords do not match.",
    )
    if problem:
        return fail(problem)
    try:
        _service.update_password(email, old_password, new_password)
        return ok("Password updated successfully.")
    except ServiceError as error:
        return fail(str(error))


def update_email(old_email, new_email, otp_code):
    if not is_valid_email(new_email):
        return fail("Please enter a valid new email address.")
    if not otp_code or not otp_code.strip():
        return fail(_NO_OTP)
    try:
        return ok("Email updated successfully.", _service.update_email(old_email, new_email, otp_code.strip()))
    except ServiceError as error:
        return fail(str(error))