"""
Auth controller tests: basic validation and message building, plus the bug fix
that a typo in the new password no longer burns the OTP. The controller's
service is swapped for one built from in-memory fakes (no database).
"""
import unittest

from backend.controllers import auth_controller as ac
from backend.services.auth_service import AuthService, OtpGenerator
from tests.test_auth_service_unit import FakeHasher, FakeOtps, FakeUsers


class AuthControllerCase(unittest.TestCase):
    def setUp(self):
        self.real = ac._service
        self.users, self.otps, self.delivered = FakeUsers(), FakeOtps(), []
        ac._service = AuthService(self.users, self.otps, hasher=FakeHasher(), otp_generator=OtpGenerator(6),
                                  deliver_otp=lambda e, c: self.delivered.append(c))
    def tearDown(self): ac._service = self.real


class TestValidation(AuthControllerCase):
    def test_register_rules_and_messages(self):
        cases = [(" ", "a@x.com", "secret1", "secret1", "Username cannot be empty."),
                 ("Ana", "not-an-email", "secret1", "secret1", "Please enter a valid email address."),
                 ("Ana", "a@x.com", "abc", "abc", "Password must be at least 6 characters long."),
                 ("Ana", "a@x.com", "secret1", "secret2", "Passwords do not match.")]
        for name, email, pw, confirm, message in cases:
            with self.subTest(message=message):
                self.assertEqual(ac.register_user(name, email, pw, confirm), (False, message, None))
        self.assertEqual(self.users.by_email, {})          # nothing was created

    def test_register_success_message(self):
        self.assertEqual(ac.register_user(" Ana ", "a@x.com", "secret1", "secret1"),
                         (True, "Account created. Please verify the OTP sent to your email.", {"email": "a@x.com"}))
        self.assertEqual(self.users.by_email["a@x.com"].full_name, "Ana")      # trimmed

    def test_empty_otp_is_rejected_before_anything_else(self):
        self.assertEqual(ac.verify_otp("a@x.com", "  "), (False, "Please enter the OTP.", None))

    def test_login_checks_the_email_format_first(self):
        self.assertEqual(ac.login_user("nope", "x"), (False, "Please enter a valid email address.", None))

    def test_update_password_messages(self):
        self.assertEqual(ac.update_password("a@x.com", "old", "abc", "abc"),
                         (False, "New password must be at least 6 characters long.", None))
        self.assertEqual(ac.update_password("a@x.com", "old", "secret1", "secret2"),
                         (False, "New passwords do not match.", None))

    def test_update_email_rejects_a_bad_new_address(self):
        self.assertEqual(ac.update_email("a@x.com", "bad", "123456"),
                         (False, "Please enter a valid new email address.", None))


class TestPasswordResetKeepsTheOtp(AuthControllerCase):
    def test_a_typo_in_the_new_password_does_not_burn_the_otp(self):
        ac.register_user("Ana", "a@x.com", "secret1", "secret1")
        ac.request_password_reset("a@x.com")
        code = self.delivered[-1]

        ok, message, _ = ac.reset_password("a@x.com", code, "newpass1", "newpass2")       # typo
        self.assertEqual((ok, message), (False, "Passwords do not match."))

        ok, message, _ = ac.reset_password("a@x.com", code, "newpass1", "newpass1")       # retry, same code
        self.assertEqual((ok, message), (True, "Password reset successfully. You can now log in."))
        self.assertTrue(ac.login_user("a@x.com", "newpass1")[0])


if __name__ == "__main__":
    unittest.main()