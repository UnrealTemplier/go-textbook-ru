"""Книжные тесты: правила go-textbook из book.toml (канонические названия, клише, выноски)."""
import os
import unittest

from engine.config import load_config, canonicalize_title
from engine.converter import MarkdownConverter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG = load_config(os.path.join(ROOT, "book.toml"))


class CanonicalTitleTest(unittest.TestCase):
    def test_rules(self):
        rules = CONFIG.content.canonical_replacements
        self.assertEqual(len(rules), 30)
        self.assertEqual(canonicalize_title("net_http_httptest", rules), "net/http/httptest")
        self.assertEqual(canonicalize_title("net_http", rules), "net/http")
        self.assertEqual(canonicalize_title("CI_CD и TCP_IP", rules), "CI/CD и TCP/IP")
        self.assertEqual(canonicalize_title("sync_pool и sync_map", rules), "sync.Pool и sync.Map")
        self.assertEqual(canonicalize_title("golang_org_x_sys", rules), "golang.org/x/sys")
        self.assertEqual(canonicalize_title("Обычное название", rules), "Обычное название")


class ClichesTest(unittest.TestCase):
    def setUp(self):
        self.conv = MarkdownConverter(None, CONFIG)

    def test_each_pattern(self):
        c = self.conv._clean_cliches
        self.assertEqual(c("В современном мире облаков, сервисы растут."), "сервисы растут.")
        self.assertEqual(c("В современном быстро меняющемся мире, код живёт."), "код живёт.")
        self.assertEqual(c("Важно понимать, что GC паузит."), "GC паузит.")
        self.assertEqual(c("Важно помнить, что x."), "x.")
        self.assertEqual(c("Как известно, CPU быстрый."), "CPU быстрый.")
        self.assertEqual(c("Не секрет, что сеть ненадёжна."), "сеть ненадёжна.")
        self.assertEqual(c("Давайте рассмотрим пример:\nкод"), "код")

    def test_case_insensitive(self):
        self.assertEqual(self.conv._clean_cliches("как известно, x"), "x")

    def test_untouched(self):
        text = "Известно, что так. Важно: ничего не трогать."
        self.assertEqual(self.conv._clean_cliches(text), text)


class CalloutHeuristicTest(unittest.TestCase):
    def test_interview_heuristic_enabled(self):
        out = MarkdownConverter(None, CONFIG)._transform_callouts("> [!tip] Собеседование\n> вопрос")
        self.assertIn('class="callout callout-interview"', out)


if __name__ == "__main__":
    unittest.main()
