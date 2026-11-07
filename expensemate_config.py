"""
expensemate_config.py
=====================
ONE place for every setting that used to be hard-coded in the source code.

Where a value comes from (first match wins):
    1. an environment variable            e.g.  EXPENSEMATE_DB=C:\\temp\\test.db
    2. the optional file  expensemate.ini  (next to app.py)
    3. the built-in default below         (= the exact value Assignment 01 used)

If a value is missing, empty, not a number or out of range, it is ignored and the
next source is tried - so a missing or broken configuration can never stop the app;
it simply behaves like Assignment 01.

Setting                   Environment variable               ini section / key              Default
------------------------  ---------------------------------  -----------------------------  ----------------
Database file             EXPENSEMATE_DB                     [database] path                expense_mate.db
OTP length (digits)       EXPENSEMATE_OTP_LENGTH             [auth] otp_length              6
OTP validity (minutes)    EXPENSEMATE_OTP_VALIDITY_MINUTES   [auth] otp_validity_minutes    10
Minimum password length   EXPENSEMATE_MIN_PASSWORD_LENGTH    [auth] min_password_length     6

A relative database path is resolved against the project folder (not the
folder you happen to run Python from).
"""

import configparser
import logging
import os
from pathlib import Path
from typing import Mapping, NamedTuple, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INI_PATH = PROJECT_ROOT / "expensemate.ini"

# Built-in defaults: identical to the values that were hard-coded in Assignment 01.
DEFAULT_DB_PATH = PROJECT_ROOT / "expense_mate.db"
DEFAULT_OTP_LENGTH = 6
DEFAULT_OTP_VALIDITY_MINUTES = 10
DEFAULT_MIN_PASSWORD_LENGTH = 6

# Allowed ranges (protect against typos such as otp_length = 0).
OTP_LENGTH_RANGE = (4, 10)
OTP_VALIDITY_RANGE = (1, 1440)          # 1 minute .. 24 hours
MIN_PASSWORD_LENGTH_RANGE = (1, 128)


class Settings(NamedTuple):
    db_path: Path
    otp_length: int
    otp_validity_minutes: int
    min_password_length: int


def _read_ini(ini_path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    try:
        if Path(ini_path).is_file():
            parser.read(ini_path, encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError) as exc:
        logger.warning("Ignoring unreadable config file %s: %s", ini_path, exc)
        return configparser.ConfigParser()
    return parser


def _candidates(env: Mapping[str, str], parser: configparser.ConfigParser,
                env_name: str, section: str, key: str):
    """Yield (source, raw_value) from the highest priority source to the lowest."""
    raw = env.get(env_name)
    if raw is not None and raw.strip():
        yield f"environment variable {env_name}", raw.strip()
    raw = parser.get(section, key, fallback=None)
    if raw is not None and raw.strip():
        yield f"expensemate.ini [{section}] {key}", raw.strip()


def _int_setting(env, parser, env_name, section, key, default, value_range) -> int:
    low, high = value_range
    for source, raw in _candidates(env, parser, env_name, section, key):
        try:
            value = int(raw)
        except ValueError:
            logger.warning("Ignoring %s = %r (not a whole number)", source, raw)
            continue
        if not low <= value <= high:
            logger.warning("Ignoring %s = %r (allowed range %d..%d)", source, raw, low, high)
            continue
        return value
    return default


def _path_setting(env, parser, env_name, section, key, default: Path) -> Path:
    for _source, raw in _candidates(env, parser, env_name, section, key):
        path = Path(os.path.expanduser(raw))
        return path if path.is_absolute() else PROJECT_ROOT / path
    return default


def load_settings(env: Optional[Mapping[str, str]] = None,
                  ini_path: Optional[Path] = None) -> Settings:
    """Build the settings. Both arguments exist so tests can inject their own."""
    env = os.environ if env is None else env
    parser = _read_ini(DEFAULT_INI_PATH if ini_path is None else ini_path)
    return Settings(
        db_path=_path_setting(env, parser, "EXPENSEMATE_DB", "database", "path", DEFAULT_DB_PATH),
        otp_length=_int_setting(env, parser, "EXPENSEMATE_OTP_LENGTH", "auth", "otp_length",
                                DEFAULT_OTP_LENGTH, OTP_LENGTH_RANGE),
        otp_validity_minutes=_int_setting(env, parser, "EXPENSEMATE_OTP_VALIDITY_MINUTES", "auth",
                                          "otp_validity_minutes", DEFAULT_OTP_VALIDITY_MINUTES,
                                          OTP_VALIDITY_RANGE),
        min_password_length=_int_setting(env, parser, "EXPENSEMATE_MIN_PASSWORD_LENGTH", "auth",
                                         "min_password_length", DEFAULT_MIN_PASSWORD_LENGTH,
                                         MIN_PASSWORD_LENGTH_RANGE),
    )


# Loaded once, when the program starts. The rest of the code imports these names.
settings = load_settings()

DB_PATH = settings.db_path
OTP_LENGTH = settings.otp_length
OTP_VALIDITY_MINUTES = settings.otp_validity_minutes
MIN_PASSWORD_LENGTH = settings.min_password_length
