"""
Unit tests for auth_service.py (Day 1: Auth Module).

Rewritten to match the contract-based version of auth_service.py
(register_user, login_user, send_otp, verify_otp, etc. — matching
backend_interface.py's (success, message, data) tuple format). The
original version of this file tested an earlier interface (register,
login, AuthError) that no longer exists in the codebase.

Run with: python -m unittest tests.test_auth_service -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import init_db, DB_PATH
from backend.repositories.user_repository import UserRepository, OtpRepository
from backend.services.auth_service import (
    register_user, send_otp, verify_otp, login_user, logout_user,
    request_password_reset, reset_password, update_password, update_email,
    is_valid_email, is_valid_password,
)


class TestAuthService(unittest.TestCase):

    def setUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        self.user_repo = UserRepository()
        self.otp_repo = OtpRepository()
        self.email = "authtest@example.com"

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def _latest_otp_code(self, email):
        user = self.user_repo.get_by_email(email)
        otp = self.otp_repo.get_latest_otp(user.user_id, "GENERAL")
        return otp.otp_code

    # ---------- Validation helpers ----------

    def test_is_valid_email_accepts_correct_format(self):
        self.assertTrue(is_valid_email("user@example.com"))

    def test_is_valid_email_rejects_bad_format(self):
        self.assertFalse(is_valid_email("not-an-email"))
        self.assertFalse(is_valid_email(""))

    def test_is_valid_password_accepts_six_or_more_chars(self):
        self.assertTrue(is_valid_password("pass12"))

    def test_is_valid_password_rejects_short_password(self):
        self.assertFalse(is_valid_password("abc"))

    # ---------- Registration ----------

    def test_register_user_success(self):
        success, message, data = register_user("Laiba", self.email, "pass123", "pass123")
        self.assertTrue(success)
        self.assertEqual(data["email"], self.email)

    def test_register_user_creates_unverified_account(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        user = self.user_repo.get_by_email(self.email)
        self.assertFalse(user.is_verified)

    def test_register_user_empty_username_fails(self):
        success, _, _ = register_user("   ", self.email, "pass123", "pass123")
        self.assertFalse(success)

    def test_register_user_invalid_email_fails(self):
        success, _, _ = register_user("Laiba", "not-an-email", "pass123", "pass123")
        self.assertFalse(success)

    def test_register_user_short_password_fails(self):
        success, _, _ = register_user("Laiba", self.email, "abc", "abc")
        self.assertFalse(success)

    def test_register_user_mismatched_passwords_fails(self):
        success, _, _ = register_user("Laiba", self.email, "pass123", "pass456")
        self.assertFalse(success)

    def test_register_user_duplicate_email_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, _, _ = register_user("Someone Else", self.email, "pass456", "pass456")
        self.assertFalse(success)

    # ---------- OTP ----------

    def test_send_otp_success_for_existing_user(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, _, _ = send_otp(self.email)
        self.assertTrue(success)

    def test_send_otp_unknown_email_fails(self):
        success, _, _ = send_otp("nobody@example.com")
        self.assertFalse(success)

    def test_verify_otp_success_with_correct_code(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        code = self._latest_otp_code(self.email)
        success, _, _ = verify_otp(self.email, code)
        self.assertTrue(success)

    def test_verify_otp_marks_user_verified(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        code = self._latest_otp_code(self.email)
        verify_otp(self.email, code)
        user = self.user_repo.get_by_email(self.email)
        self.assertTrue(user.is_verified)

    def test_verify_otp_wrong_code_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, _, _ = verify_otp(self.email, "000000")
        self.assertFalse(success)

    def test_verify_otp_cannot_be_reused(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        code = self._latest_otp_code(self.email)
        verify_otp(self.email, code)
        success, _, _ = verify_otp(self.email, code)
        self.assertFalse(success)

    def test_verify_otp_empty_code_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, _, _ = verify_otp(self.email, "")
        self.assertFalse(success)

    # ---------- Login ----------

    def test_login_success_with_correct_credentials(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, message, data = login_user(self.email, "pass123")
        self.assertTrue(success)
        self.assertEqual(data["email"], self.email)

    def test_login_wrong_password_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, _, _ = login_user(self.email, "wrongpass")
        self.assertFalse(success)

    def test_login_unknown_email_fails(self):
        success, _, _ = login_user("nobody@example.com", "pass123")
        self.assertFalse(success)

    def test_login_invalid_email_format_fails(self):
        success, _, _ = login_user("not-an-email", "pass123")
        self.assertFalse(success)

    def test_logout_clears_session(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        login_user(self.email, "pass123")
        success, _, _ = logout_user()
        self.assertTrue(success)

    # ---------- Forgot / reset password ----------

    def test_request_password_reset_known_email_succeeds(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, _, _ = request_password_reset(self.email)
        self.assertTrue(success)

    def test_request_password_reset_unknown_email_fails(self):
        success, _, _ = request_password_reset("nobody@example.com")
        self.assertFalse(success)

    def test_reset_password_success_flow(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        request_password_reset(self.email)
        code = self._latest_otp_code(self.email)

        success, _, _ = reset_password(self.email, code, "newpass1", "newpass1")
        self.assertTrue(success)

        success, _, _ = login_user(self.email, "newpass1")
        self.assertTrue(success)

    def test_reset_password_mismatched_new_passwords_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        request_password_reset(self.email)
        code = self._latest_otp_code(self.email)
        success, _, _ = reset_password(self.email, code, "newpass1", "different1")
        self.assertFalse(success)

    def test_reset_password_wrong_otp_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        request_password_reset(self.email)
        success, _, _ = reset_password(self.email, "000000", "newpass1", "newpass1")
        self.assertFalse(success)

    # ---------- Update password (while logged in) ----------

    def test_update_password_success(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, _, _ = update_password(self.email, "pass123", "newpass1", "newpass1")
        self.assertTrue(success)
        success, _, _ = login_user(self.email, "newpass1")
        self.assertTrue(success)

    def test_update_password_wrong_current_password_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, _, _ = update_password(self.email, "wrongpass", "newpass1", "newpass1")
        self.assertFalse(success)

    def test_update_password_mismatched_new_passwords_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        success, _, _ = update_password(self.email, "pass123", "newpass1", "different1")
        self.assertFalse(success)

    # ---------- Update email ----------

    def test_update_email_success(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        code = self._latest_otp_code(self.email)  # OTP from registration
        send_otp(self.email)  # fresh OTP for the email-change verification
        code = self._latest_otp_code(self.email)

        success, _, data = update_email(self.email, "newemail@example.com", code)
        self.assertTrue(success)
        self.assertEqual(data["email"], "newemail@example.com")

    def test_update_email_to_existing_email_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        register_user("Sib", "sib@example.com", "pass123", "pass123")
        send_otp(self.email)
        code = self._latest_otp_code(self.email)

        success, _, _ = update_email(self.email, "sib@example.com", code)
        self.assertFalse(success)

    def test_update_email_invalid_new_email_fails(self):
        register_user("Laiba", self.email, "pass123", "pass123")
        send_otp(self.email)
        code = self._latest_otp_code(self.email)
        success, _, _ = update_email(self.email, "not-an-email", code)
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()