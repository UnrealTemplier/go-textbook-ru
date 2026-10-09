"""Тесты чтения версии книги: version или version_file + version_pattern (book.toml)."""
import os
import tempfile
import unittest

from engine.config import BookConfig, ProjectConfig
from engine.template import get_project_version, get_book_version

PATTERN = r"^\s*[-*]?\s*\*\*Current project version:\*\*\s*`?([0-9A-Za-z.-]+)`?"


class VersionFileTest(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "AGENTS.md")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(text)
            return get_project_version(path, PATTERN)

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
            get_project_version("/nonexistent/AGENTS.md", PATTERN)


class BookVersionTest(unittest.TestCase):
    def test_inline_version(self):
        self.assertEqual(get_book_version(BookConfig(project=ProjectConfig(version="1.0.0"))), "1.0.0")
        with self.assertRaisesRegex(ValueError, "Invalid"):
            get_book_version(BookConfig(project=ProjectConfig(version="v1")))

    def test_no_version(self):
        with self.assertRaisesRegex(ValueError, "не задана"):
            get_book_version(BookConfig())


if __name__ == "__main__":
    unittest.main()
