"""Характеризационные тесты чтения версии проекта из AGENTS.md (§ 1.4)."""
import os
import tempfile
import unittest

from engine.template import get_project_version


class VersionTest(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "AGENTS.md")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(text)
            return get_project_version(path)

    def test_single_declaration(self):
        self.assertEqual(self.read("x\n* **Current project version:** `1.2.3`\n"), "1.2.3")
        self.assertEqual(self.read("* **Current project version:** `2.0.0-rc.1`\n"), "2.0.0-rc.1")

    def test_errors(self):
        with self.assertRaisesRegex(ValueError, "VERSION ERROR"):
            self.read("нет версии\n")
        with self.assertRaisesRegex(ValueError, "Multiple"):
            self.read("* **Current project version:** `1.0.0`\n* **Current project version:** `1.0.1`\n")
        with self.assertRaisesRegex(ValueError, "Invalid"):
            self.read("* **Current project version:** `1.0`\n")

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            get_project_version("/nonexistent/AGENTS.md")

    def test_repository_version(self):
        self.assertRegex(get_project_version(), r"^\d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
