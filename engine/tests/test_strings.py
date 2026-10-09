"""Тесты словаря строк интерфейса (engine/strings/ru.toml) и переопределений книги."""
import os
import tempfile
import unittest

from engine.config import BookConfig, ConfigError, default_strings, load_config
from engine.converter import MarkdownConverter


class StringsTest(unittest.TestCase):
    def test_defaults_and_substitution(self):
        cfg = BookConfig()
        self.assertEqual(cfg.t("article.module_tag", n=7), "Модуль 7")
        self.assertEqual(cfg.t("callouts.note"), "Заметка")
        self.assertGreater(len(default_strings()), 50)

    def test_book_override(self):
        cfg = BookConfig(strings={"callouts": {"note": "Примечание"}})
        self.assertEqual(cfg.t("callouts.note"), "Примечание")
        out = MarkdownConverter(None, cfg)._transform_callouts("> [!note]\n> x")
        self.assertIn('aria-label="Примечание"', out)

    def test_unknown_key_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "book.toml")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write('[strings.callouts]\nnotee = "x"\n')
            with self.assertRaisesRegex(ConfigError, "strings: неизвестные ключи"):
                load_config(path)

    def test_non_string_value_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "book.toml")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write('[strings.article]\nmodule_tag = 5\n')
            with self.assertRaisesRegex(ConfigError, "ожидается строка"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
