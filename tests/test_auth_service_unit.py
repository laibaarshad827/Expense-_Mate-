"""
Unit tests for the rewritten AuthService.
Everything is injected: in-memory repositories, a fake password hasher (no slow
bcrypt), a fake clock (so OTP expiry can be tested) and a list that collects
the 'delivered' OTP codes. No database, no printing, no waiting.
"""
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

from backend.errors import ServiceError
from backend.services.auth_service import AuthService, OtpGenerator, PasswordHasher


class FakeUsers:
    def __init__(self):
        self.by_email, self.next_id = {}, 1
    def get_by_email(self, email): return self.by_email.get(email)
    def create_user(self, name, email, password_hash):
        user = SimpleNamespace(user_id=self.next_id, full_name=name, email=email,
                               password_hash=password_hash, is_verified=False)
        self.by_email[email] = user; self.next_id += 1
        return user.user_id
    def set_verified(self, uid): self._by_id(uid).is_verified = True
    def update_password(self, uid, new_hash): self._by_id(uid).password_hash = new_hash
    def update_email(self, uid, new_email):
        user = self._by_id(uid); del self.by_email[user.email]
        user.email = new_email; self.by_email[new_email] = user
    def _by_id(self, uid): return next(u for u in self.by_email.values() if u.user_id == uid)


class FakeOtps:
    def __init__(self): self.rows = []
    def create_otp(self, uid, code, purpose, expires_at):
        self.rows.append(SimpleNamespace(otp_id=len(self.rows) + 1, user_id=uid, otp_code=code,
                                         purpose=purpose, expires_at=expires_at, is_used=False))
    def get_latest_otp(self, uid, purpose):
        mine = [r for r in self.rows if r.user_id == uid and r.purpose == purpose]
        return mine[-1] if mine else None
    def mark_used(self, otp_id): next(r for r in self.rows if r.otp_id == otp_id).is_used = True


class FakeHasher:
    def hash(self, password): return "hashed:" + password
    def verify(self, password, password_hash): return password_hash == "hashed:" + password


class Env:
    """Builds an AuthService wired to fakes and exposes the pieces the tests need."""
    def __init__(self):
        self.users, self.otps, self.delivered = FakeUsers(), FakeOtps(), []
        self.now = datetime(2026, 1, 1, 12, 0, 0)
        self.service = AuthService(
            self.users, self.otps, hasher=FakeHasher(), otp_generator=OtpGenerator(6),
            deliver_otp=lambda email, code: self.delivered.append((email, code)),
            clock=lambda: self.now, otp_validity_minutes=10)
    @property
    def last_code(self): return self.delivered[-1][1]


def registered():
    env = Env()
    env.service.register("Ana", "ana@x.com", "secret1")
    return env


class TestRegistration(unittest.TestCase):
    def test_register_stores_a_hash_not_the_password_and_sends_an_otp(self):
        env = registered()
        user = env.users.by_email["ana@x.com"]
        self.assertEqual(user.password_hash, "hashed:secret1")
        self.assertNotEqual(user.password_hash, "secret1")
        self.assertFalse(user.is_verified)
        self.assertEqual(len(env.delivered), 1)

    def test_duplicate_email_is_rejected(self):
        env = registered()
        with self.assertRaises(ServiceError) as ctx:
            env.service.register("Other", "ana@x.com", "secret2")
        self.assertEqual(str(ctx.exception), "An account with this email already exists.")


class TestOtp(unittest.TestCase):
    def test_correct_code_verifies_and_marks_user_verified(self):
        env = registered()
        env.service.verify_otp("ana@x.com", env.last_code)
        self.assertTrue(env.users.by_email["ana@x.com"].is_verified)

    def test_wrong_code_is_rejected(self):
        env = registered()
        with self.assertRaises(ServiceError) as ctx:
            env.service.verify_otp("ana@x.com", "000000" if env.last_code != "000000" else "111111")
        self.assertEqual(str(ctx.exception), "Incorrect OTP. Please try again.")

    def test_code_cannot_be_used_twice(self):
        env = registered()
        code = env.last_code
        env.service.verify_otp("ana@x.com", code)
        with self.assertRaises(ServiceError) as ctx:
            env.service.verify_otp("ana@x.com", code)
        self.assertEqual(str(ctx.exception), "This OTP has already been used.")

    def test_code_expires_after_the_validity_window(self):          # was untestable before
        env = registered()
        env.now += timedelta(minutes=10, seconds=1)
        with self.assertRaises(ServiceError) as ctx:
            env.service.verify_otp("ana@x.com", env.last_code)
        self.assertEqual(str(ctx.exception), "This OTP has expired. Please request a new one.")

    def test_code_is_still_valid_inside_the_window(self):
        env = registered()
        env.now += timedelta(minutes=9, seconds=59)
        env.service.verify_otp("ana@x.com", env.last_code)

    def test_resend_replaces_the_old_code(self):
        env = registered()
        old = env.last_code
        env.service.send_otp("ana@x.com")
        new = env.last_code
        if old != new:
            with self.assertRaises(ServiceError):
                env.service.verify_otp("ana@x.com", old)
        env.service.verify_otp("ana@x.com", new)

    def test_unknown_user_and_missing_otp(self):
        env = Env()
        with self.assertRaises(ServiceError) as ctx:
            env.service.verify_otp("ghost@x.com", "123456")
        self.assertEqual(str(ctx.exception), "No account found with this email.")
        env.users.create_user("Bob", "bob@x.com", "hashed:x")
        with self.assertRaises(ServiceError) as ctx:
            env.service.verify_otp("bob@x.com", "123456")
        self.assertEqual(str(ctx.exception), "No OTP was requested for this email.")


class TestLogin(unittest.TestCase):
    def test_login_sets_and_logout_clears_the_session(self):
        env = registered()
        self.assertEqual(env.service.login("ana@x.com", "secret1"), {"username": "Ana", "email": "ana@x.com"})
        self.assertEqual(env.service.current_email, "ana@x.com")
        env.service.logout()
        self.assertIsNone(env.service.current_email)

    def test_wrong_password_and_unknown_user(self):
        env = registered()
        with self.assertRaises(ServiceError) as ctx:
            env.service.login("ana@x.com", "nope")
        self.assertEqual(str(ctx.exception), "Incorrect password.")
        self.assertIsNone(env.service.current_email)
        with self.assertRaises(ServiceError):
            env.service.login("ghost@x.com", "secret1")


class TestPasswordsAndEmail(unittest.TestCase):
    def test_reset_password_uses_the_otp_once(self):
        env = registered()
        env.service.request_password_reset("ana@x.com")
        env.service.reset_password("ana@x.com", env.last_code, "newpass1")
        self.assertEqual(env.users.by_email["ana@x.com"].password_hash, "hashed:newpass1")
        with self.assertRaises(ServiceError):
            env.service.reset_password("ana@x.com", env.last_code, "another1")

    def test_failed_reset_leaves_the_password_alone(self):
        env = registered()
        env.service.request_password_reset("ana@x.com")
        with self.assertRaises(ServiceError):
            env.service.reset_password("ana@x.com", "badbad", "newpass1")
        self.assertEqual(env.users.by_email["ana@x.com"].password_hash, "hashed:secret1")

    def test_update_password_needs_the_current_password(self):
        env = registered()
        with self.assertRaises(ServiceError) as ctx:
            env.service.update_password("ana@x.com", "wrong", "newpass1")
        self.assertEqual(str(ctx.exception), "Current password is incorrect.")
        env.service.update_password("ana@x.com", "secret1", "newpass1")
        self.assertEqual(env.users.by_email["ana@x.com"].password_hash, "hashed:newpass1")

    def test_update_password_unknown_user(self):
        with self.assertRaises(ServiceError) as ctx:
            Env().service.update_password("ghost@x.com", "a", "b")
        self.assertEqual(str(ctx.exception), "User not found.")

    def test_update_email_success_and_in_use(self):
        env = registered()
        env.service.register("Bob", "bob@x.com", "secret2")
        env.service.send_otp("ana@x.com")
        with self.assertRaises(ServiceError) as ctx:
            env.service.update_email("ana@x.com", "bob@x.com", env.last_code)
        self.assertEqual(str(ctx.exception), "This email is already in use.")
        self.assertEqual(env.service.update_email("ana@x.com", "new@x.com", env.last_code), {"email": "new@x.com"})
        self.assertIn("new@x.com", env.users.by_email)

    def test_update_email_with_wrong_code_changes_nothing(self):
        env = registered()
        env.service.send_otp("ana@x.com")
        with self.assertRaises(ServiceError):
            env.service.update_email("ana@x.com", "new@x.com", "badbad")
        self.assertIn("ana@x.com", env.users.by_email)


class TestHelpers(unittest.TestCase):
    def test_otp_generator_makes_codes_of_the_requested_length_without_leading_zero(self):
        for length in (4, 6, 8):
            gen = OtpGenerator(length)
            for _ in range(300):
                code = gen.generate()
                self.assertEqual(len(code), length)
                self.assertNotEqual(code[0], "0")
                self.assertTrue(code.isdigit())

    def test_password_hasher_round_trip(self):
        hasher = PasswordHasher()
        hashed = hasher.hash("secret1")
        self.assertNotEqual(hashed, "secret1")
        self.assertTrue(hasher.verify("secret1", hashed))
        self.assertFalse(hasher.verify("secret2", hashed))


if __name__ == "__main__":
    unittest.main()