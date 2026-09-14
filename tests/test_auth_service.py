"""
Unit tests for AuthService.
Run with: python -m unittest discover tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import init_db, DB_PATH
from backend.services.auth_service import AuthService, AuthError


class TestAuthService(unittest.TestCase):

    def setUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        self.auth = AuthService()

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_register_creates_unverified_user(self):
        user_id = self.auth.register("Laiba Arshad", "laiba@example.com", "Passw0rd")
        self.assertIsInstance(user_id, int)
        user = self.auth.user_repo.get_by_id(user_id)
        self.assertFalse(user.is_verified)

    def test_register_duplicate_email_fails(self):
        self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        with self.assertRaises(AuthError):
            self.auth.register("Another Name", "laiba@example.com", "Passw0rd2")

    def test_register_weak_password_fails(self):
        with self.assertRaises(AuthError):
            self.auth.register("Laiba", "laiba@example.com", "weak")

    def test_register_invalid_email_fails(self):
        with self.assertRaises(AuthError):
            self.auth.register("Laiba", "not-an-email", "Passw0rd")

    def test_verify_registration_otp_success(self):
        user_id = self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        otp = self.auth.otp_repo.get_latest_otp(user_id, "REGISTER")
        self.auth.verify_registration_otp(user_id, otp.otp_code)
        user = self.auth.user_repo.get_by_id(user_id)
        self.assertTrue(user.is_verified)

    def test_verify_registration_otp_wrong_code_fails(self):
        user_id = self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        with self.assertRaises(AuthError):
            self.auth.verify_registration_otp(user_id, "000000")

    def test_otp_cannot_be_reused(self):
        user_id = self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        otp = self.auth.otp_repo.get_latest_otp(user_id, "REGISTER")
        self.auth.verify_registration_otp(user_id, otp.otp_code)
        with self.assertRaises(AuthError):
            self.auth.verify_otp(user_id, "REGISTER", otp.otp_code)

    def test_login_before_verification_fails(self):
        self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        with self.assertRaises(AuthError):
            self.auth.login("laiba@example.com", "Passw0rd")

    def test_login_success_after_verification(self):
        user_id = self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        otp = self.auth.otp_repo.get_latest_otp(user_id, "REGISTER")
        self.auth.verify_registration_otp(user_id, otp.otp_code)
        user = self.auth.login("laiba@example.com", "Passw0rd")
        self.assertEqual(user.email, "laiba@example.com")

    def test_login_wrong_password_fails(self):
        user_id = self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        otp = self.auth.otp_repo.get_latest_otp(user_id, "REGISTER")
        self.auth.verify_registration_otp(user_id, otp.otp_code)
        with self.assertRaises(AuthError):
            self.auth.login("laiba@example.com", "WrongPass1")

    def test_password_reset_flow(self):
        user_id = self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        reg_otp = self.auth.otp_repo.get_latest_otp(user_id, "REGISTER")
        self.auth.verify_registration_otp(user_id, reg_otp.otp_code)
        self.auth.request_password_reset("laiba@example.com")
        reset_otp = self.auth.otp_repo.get_latest_otp(user_id, "RESET_PASSWORD")
        self.auth.reset_password(user_id, reset_otp.otp_code, "NewPass1")
        user = self.auth.login("laiba@example.com", "NewPass1")
        self.assertEqual(user.user_id, user_id)

    def test_update_password_with_wrong_current_fails(self):
        user_id = self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        otp = self.auth.otp_repo.get_latest_otp(user_id, "REGISTER")
        self.auth.verify_registration_otp(user_id, otp.otp_code)
        with self.assertRaises(AuthError):
            self.auth.update_password(user_id, "WrongCurrent1", "NewPass1")

    def test_update_email_success(self):
        user_id = self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        self.auth.update_email(user_id, "new@example.com")
        user = self.auth.user_repo.get_by_id(user_id)
        self.assertEqual(user.email, "new@example.com")

    def test_update_email_to_existing_fails(self):
        self.auth.register("Laiba", "laiba@example.com", "Passw0rd")
        user_id_2 = self.auth.register("Sib", "sib@example.com", "Passw0rd")
        with self.assertRaises(AuthError):
            self.auth.update_email(user_id_2, "laiba@example.com")


if __name__ == "__main__":
    unittest.main()