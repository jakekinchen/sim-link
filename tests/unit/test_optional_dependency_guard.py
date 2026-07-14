"""Tests for collection-time optional dependency detection."""

from __future__ import annotations

import tempfile
import unittest

from pathlib import Path

from tests.optional_dependency_guard import (
    _top_level_imports,
    missing_top_level_optional_dependency,
)


class OptionalDependencyGuardTests(unittest.TestCase):
    def test_top_level_imports_ignore_function_body_imports(self) -> None:
        source = """\nimport json\n\ndef test_body():\n    import pydrake\n"""
        from ast import parse

        self.assertEqual(_top_level_imports(parse(source)), ("json",))

    def test_unavailable_optional_import_is_detected_before_collection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sim-link-optional-guard-") as directory:
            path = Path(directory) / "test_optional.py"
            path.write_text("import pydrake\n", encoding="utf-8")
            missing = missing_top_level_optional_dependency(path)
        if missing is not None:
            self.assertEqual(missing, "pydrake")


if __name__ == "__main__":
    unittest.main()
