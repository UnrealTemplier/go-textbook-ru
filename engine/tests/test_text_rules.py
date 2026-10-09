"""Характеризационные тесты текстовых правил движка: slug, канонические названия, клише.

Ожидаемые значения сняты с текущего поведения. Тест падает, если поведение изменилось:
для go-textbook это изменило бы URL, якоря или видимый текст.
"""
import unittest

from engine.config import canonicalize_title
from engine.scanner import slugify, normalize_key
from engine.converter import MarkdownConverter


class SlugifyTest(unittest.TestCase):
    def test_transliteration_and_separators(self):
        self.assertEqual(slugify("Привет, мир!"), "privet-mir")
        self.assertEqual(slugify("Ёжик в тумане"), "yozhik-v-tumane")
        self.assertEqual(slugify("Щука_съела.ёлку"), "shchuka-sela-yolku")
        self.assertEqual(slugify("C++ и C#"), "c-i-c")
        self.assertEqual(slugify("4. Linux /proc/[pid]/maps и perf", 80), "4-linux-procpidmaps-i-perf")
        self.assertEqual(slugify("Как правильно follow-up`ить после интервью?", 80),
                         "kak-pravilno-follow-upit-posle-intervyu")

    def test_empty_and_symbols(self):
        self.assertEqual(slugify(""), "item")
        self.assertEqual(slugify("!!!"), "item")
        self.assertEqual(slugify("  -- a -- "), "a")

    def test_lengths_by_level(self):
        title = "Сравнение подходов: Go против PHP и C#"
        expected = {
            20: "sravnenie-podkhodov",          # под-подраздел (первая часть)
            25: "sravnenie-podkhodov-go-pr",    # под-подраздел (вторая часть)
            35: "sravnenie-podkhodov-go-protiv-php-i",  # модуль, подраздел
            55: "sravnenie-podkhodov-go-protiv-php-i-c",  # файл
            60: "sravnenie-podkhodov-go-protiv-php-i-c",  # значение по умолчанию
            80: "sravnenie-podkhodov-go-protiv-php-i-c",  # якорь
        }
        for length, slug in expected.items():
            self.assertEqual(slugify(title, length), slug, length)
        self.assertEqual(slugify(title), expected[60])

    def test_truncation_strips_trailing_dash(self):
        self.assertEqual(slugify("net_http и sync_atomic", 20), "net-http-i-sync-atom")
        self.assertFalse(slugify("ab cd", 3).endswith("-"))


class CanonicalTitleTest(unittest.TestCase):
    def test_ordered_whole_word_replacements(self):
        rules = [("net_http_httptest", "net/http/httptest"), ("net_http", "net/http"), ("a_b", "x\\y")]
        self.assertEqual(canonicalize_title("net_http_httptest и net_http", rules), "net/http/httptest и net/http")
        self.assertEqual(canonicalize_title("net_https", rules), "net_https")      # только целое слово
        self.assertEqual(canonicalize_title("a_b", rules), "x\\y")              # замена — буквальный текст
        self.assertEqual(canonicalize_title("net_http", []), "net_http")

    def test_normalize_key(self):
        self.assertEqual(normalize_key("24. Long polling.md"), "24 long polling")


class ClichesDefaultTest(unittest.TestCase):
    def test_engine_default_is_empty(self):
        text = "Как известно, CPU быстрый."
        self.assertEqual(MarkdownConverter(None)._clean_cliches(text), text)


if __name__ == "__main__":
    unittest.main()
