
"""
Tests for the configuration migration (Assignment 02, Part A).
Run with: python -m unittest tests.test_config -v
"""

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import expensemate_config as cfg
from expensemate_config import load_settings
from backend import validators
from backend.controllers import auth_controller
from backend.services.auth_service import OtpGenerator


class TestLoadSettings(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ini = Path(self.tmp.name) / "test.ini"

    def tearDown(self):
        self.tmp.cleanup()

    def write_ini(self, text):
        self.ini.write_text(text, encoding="utf-8")

    def test_defaults_equal_the_assignment_01_values(self):
        s = load_settings(env={}, ini_path=Path(self.tmp.name) / "missing.ini")
        self.assertEqual(s.db_path, cfg.PROJECT_ROOT / "expense_mate.db")
        self.assertEqual(s.otp_length, 6)
        self.assertEqual(s.otp_validity_minutes, 10)
        self.assertEqual(s.min_password_length, 6)

    def test_shipped_ini_file_equals_the_defaults(self):
        shipped = load_settings(env={})
        defaults = load_settings(env={}, ini_path=Path(self.tmp.name) / "missing.ini")
        self.assertEqual(shipped, defaults)

    def test_environment_variable_overrides_database_path(self):
        s = load_settings(env={"EXPENSEMATE_DB": os.path.join(self.tmp.name, "x.db")},
                          ini_path=self.ini)
        self.assertEqual(s.db_path, Path(self.tmp.name) / "x.db")

    def test_ini_file_overrides_defaults(self):
        self.write_ini("[auth]\notp_length = 8\notp_validity_minutes = 5\nmin_password_length = 10\n"
                       "[database]\npath = data/other.db\n")
        s = load_settings(env={}, ini_path=self.ini)
        self.assertEqual((s.otp_length, s.otp_validity_minutes, s.min_password_length), (8, 5, 10))
        self.assertEqual(s.db_path, cfg.PROJECT_ROOT / "data" / "other.db")

    def test_environment_beats_ini(self):
        self.write_ini("[auth]\nmin_password_length = 10\n")
        s = load_settings(env={"EXPENSEMATE_MIN_PASSWORD_LENGTH": "12"}, ini_path=self.ini)
        self.assertEqual(s.min_password_length, 12)

    def test_invalid_values_fall_back_without_crashing(self):
        self.write_ini("[auth]\notp_length = abc\notp_validity_minutes = 0\nmin_password_length = 99999\n")
        with self.assertLogs("expensemate_config", level="WARNING"):
            s = load_settings(env={}, ini_path=self.ini)
        self.assertEqual((s.otp_length, s.otp_validity_minutes, s.min_password_length), (6, 10, 6))

    def test_bad_environment_value_falls_through_to_ini(self):
        self.write_ini("[auth]\notp_length = 8\n")
        with self.assertLogs("expensemate_config", level="WARNING"):
            s = load_settings(env={"EXPENSEMATE_OTP_LENGTH": "banana"}, ini_path=self.ini)
        self.assertEqual(s.otp_length, 8)

    def test_empty_environment_value_is_ignored(self):
        s = load_settings(env={"EXPENSEMATE_DB": "   "}, ini_path=Path(self.tmp.name) / "missing.ini")
        self.assertEqual(s.db_path, cfg.DEFAULT_DB_PATH)

    def test_corrupt_ini_file_is_ignored(self):
        self.write_ini("this is [not valid ini\n=== garbage")
        with self.assertLogs("expensemate_config", level="WARNING"):
            s = load_settings(env={}, ini_path=self.ini)
        self.assertEqual(s.otp_length, 6)


class TestApplicationUsesConfiguration(unittest.TestCase):
    """The running code really reads the configured values."""

    def test_tests_run_on_a_temporary_database_not_the_real_one(self):
        from database.database import DB_PATH
        self.assertNotEqual(Path(DB_PATH), cfg.DEFAULT_DB_PATH)
        self.assertEqual(Path(DB_PATH), Path(os.environ["EXPENSEMATE_DB"]))

    def test_generated_otp_has_configured_length(self):
        for _ in range(200):
            code = OtpGenerator().generate()
            self.assertRegex(code, rf"^[1-9][0-9]{{{cfg.OTP_LENGTH - 1}}}$")

    def test_otp_generation_follows_a_changed_length(self):
        self.assertEqual(OtpGenerator().length, cfg.OTP_LENGTH)
        self.assertEqual(len(OtpGenerator(length=8).generate()), 8)

    def test_password_rule_and_messages_use_the_configured_minimum(self):
        n = cfg.MIN_PASSWORD_LENGTH
        self.assertTrue(validators.is_valid_password("x" * n))
        self.assertFalse(validators.is_valid_password("x" * (n - 1)))
        ok, msg, _ = auth_controller.register_user("A", "a@example.com", "x" * (n - 1), "x" * (n - 1))
        self.assertFalse(ok)
        self.assertEqual(msg, f"Password must be at least {n} characters long.")

    def test_default_messages_are_unchanged_from_assignment_01(self):
        self.assertEqual(cfg.MIN_PASSWORD_LENGTH, 6)
        ok, msg, _ = auth_controller.register_user("A", "a@example.com", "12345", "12345")
        self.assertEqual(msg, "Password must be at least 6 characters long.")


if __name__ == "__main__":
    unittest.main()
