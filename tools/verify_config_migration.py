"""
Repeatable verification for the configuration migration (Assignment 02, Part A).

What it proves
--------------
Running the whole test-suite must NOT touch the real database (expense_mate.db).
Before the migration, the tests deleted that file because the app and the tests
shared one hard-coded path.

What it does
------------
1. Records the real database's table row counts and SHA-256 fingerprint.
2. Runs:  python -m unittest discover   (tests use a temporary database)
3. Records the same things again and compares them.

Run from the project folder:   python tools/verify_config_migration.py
(The evidence is also saved to docs/config_migration_evidence.txt)
"""

import hashlib
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Look at the REAL database: ignore any EXPENSEMATE_DB set in this shell.
os.environ.pop("EXPENSEMATE_DB", None)
from expensemate_config import DB_PATH  # noqa: E402

EVIDENCE_FILE = PROJECT_ROOT / "docs" / "config_migration_evidence.txt"
lines = []


def say(text=""):
    print(text)
    lines.append(text)


def snapshot(path: Path) -> dict:
    """Row counts per table + file fingerprint, read-only (never modifies the DB)."""
    if not path.exists():
        return {"exists": False, "sha256": None, "counts": {}}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        counts = {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    finally:
        conn.close()
    return {"exists": True, "sha256": digest, "counts": counts}


def show(title: str, snap: dict) -> None:
    say(f"{title}")
    if not snap["exists"]:
        say("   (database file does not exist)")
        return
    for table, count in snap["counts"].items():
        say(f"   {table:<14} {count:>5} rows")
    say(f"   fingerprint    {snap['sha256'][:16]}...")


def main() -> int:
    say("ExpenseMate - configuration migration verification")
    say(f"Date            : {datetime.now():%Y-%m-%d %H:%M:%S}")
    say(f"Real database   : {DB_PATH}")
    say("")

    before = snapshot(DB_PATH)
    show("BEFORE running the tests:", before)
    say("")

    say("Running: python -m unittest discover  (this takes about a minute) ...")
    env = os.environ.copy()
    env.pop("EXPENSEMATE_DB", None)  # tests/__init__.py must supply the temporary path itself
    result = subprocess.run([sys.executable, "-m", "unittest", "discover"],
                            cwd=PROJECT_ROOT, env=env, capture_output=True, text=True)
    summary = [ln for ln in result.stderr.splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    for ln in summary:
        say(f"   {ln}")
    say("")

    after = snapshot(DB_PATH)
    show("AFTER running the tests:", after)
    say("")

    tests_ok = result.returncode == 0
    untouched = before == after
    say(f"All tests passed          : {'YES' if tests_ok else 'NO'}")
    say(f"Real database untouched   : {'YES - identical row counts and fingerprint' if untouched else 'NO - it changed!'}")
    verdict = tests_ok and untouched
    say(f"RESULT                    : {'PASS' if verdict else 'FAIL'}")

    EVIDENCE_FILE.parent.mkdir(exist_ok=True)
    EVIDENCE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not tests_ok:
        print(result.stderr[-3000:])
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
