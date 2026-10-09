"""Характеризационные тесты текстовых правил генератора: slug, канонические названия, клише.

Ожидаемые значения сняты с текущего поведения. Тест падает, если поведение изменилось:
для go-textbook это изменило бы URL, якоря или видимый текст.
"""
import unittest

from engine.scanner import slugify, canonicalize_title, normalize_key
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
    def test_rules(self):
        self.assertEqual(canonicalize_title("net_http_httptest"), "net/http/httptest")
        self.assertEqual(canonicalize_title("net_http"), "net/http")
        self.assertEqual(canonicalize_title("CI_CD и TCP_IP"), "CI/CD и TCP/IP")
        self.assertEqual(canonicalize_title("sync_pool и sync_map"), "sync.Pool и sync.Map")
        self.assertEqual(canonicalize_title("golang_org_x_sys"), "golang.org/x/sys")
        self.assertEqual(canonicalize_title("Обычное название"), "Обычное название")

    def test_normalize_key(self):
        self.assertEqual(normalize_key("24. Long polling.md"), "24 long polling")


class ClichesTest(unittest.TestCase):
    def setUp(self):
        self.conv = MarkdownConverter(None)

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


if __name__ == "__main__":
    unittest.main()
