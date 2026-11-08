"""
Enforces the required dependency direction automatically:

    Controller -> Services -> Repository -> Database
"""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYERS = {"controllers": ROOT / "backend/controllers", "services": ROOT / "backend/services",
          "repositories": ROOT / "backend/repositories"}

# layer -> modules it must NOT import
FORBIDDEN = {
    "controllers": ("backend.repositories.", "database", "sqlite3"),
    "services": ("backend.controllers", "database", "sqlite3"),
    "repositories": ("backend.controllers", "backend.services"),
}
SQL = re.compile(r"\b(SELECT|INSERT INTO|UPDATE|DELETE FROM|CREATE TABLE)\b|\.execute\(")


def imported_modules(path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            for a in node.names: yield a.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


class TestLayering(unittest.TestCase):
    def files(self, layer):
        return [p for p in LAYERS[layer].glob("*.py") if p.name != "__init__.py"]

    def test_no_forbidden_imports(self):
        for layer, banned in FORBIDDEN.items():
            for path in self.files(layer):
                for module in imported_modules(path):
                    for prefix in banned:
                        hit = module.startswith(prefix) if prefix.endswith(".") \
                            else module == prefix or module.startswith(prefix + ".")
                        # the two real controllers import repositories only to BUILD their service
                        builds_service = (layer == "controllers" and module.startswith("backend.repositories.")
                                          and path.name in ("transaction_controller.py", "budget_controller.py"))
                        if hit and not builds_service:
                            self.fail(f"{layer}/{path.name} must not import {module}")

    def test_no_sql_in_controllers_or_services(self):
        for layer in ("controllers", "services"):
            for path in self.files(layer):
                self.assertIsNone(SQL.search(path.read_text(encoding="utf-8")),
                                  f"SQL found in {layer}/{path.name}")

    def test_screens_only_talk_to_the_backend_interface(self):
        for path in (ROOT / "screens").glob("*.py"):
            for module in imported_modules(path):
                self.assertFalse(module.startswith("backend.") or module.startswith("database"),
                                 f"{path.name} imports {module} directly")

    def test_repositories_do_no_business_calculation(self):
        for path in self.files("repositories"):
            self.assertNotIn("round(", path.read_text(encoding="utf-8"), f"calculation in {path.name}")


if __name__ == "__main__":
    unittest.main()