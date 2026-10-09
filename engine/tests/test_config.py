"""Тесты загрузки book.toml (engine/config.py)."""
import os
import tempfile
import unittest

from engine.config import ConfigError, load_config, BookConfig


class LoadConfigTest(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "book.toml")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(text)
            cfg = load_config(path)
            self.assertEqual(cfg.root_dir, tmp)
            return cfg

    def test_defaults(self):
        cfg = self.load("")
        self.assertEqual(cfg.content.root, "sources")
        self.assertEqual(cfg.content.canonical_replacements, [])
        self.assertEqual(cfg.content.clean_cliches, [])
        self.assertEqual(cfg.slug.subsection, (20, 25))
        self.assertFalse(cfg.callouts.interview_heuristic)
        self.assertEqual((cfg.navigation.reading_time.divisor, cfg.navigation.reading_time.min), (800, 2))

    def test_values_and_helpers(self):
        cfg = self.load('[project]\nstorage_prefix = "book_"\nversion = "1.2.3"\n'
                        '[content]\ncanonical_replacements = [["a_b", "a/b"]]\n[slug]\nsubsection = [10, 12]\n')
        self.assertEqual(cfg.storage_key("theme"), "book_theme")
        self.assertEqual(cfg.content.canonical_replacements, [("a_b", "a/b")])
        self.assertEqual(cfg.slug.subsection, (10, 12))
        self.assertTrue(cfg.path("x").endswith("/x"))

    def test_unknown_keys(self):
        for text in ("[project]\nversio = '1'\n", "[contnet]\nroot = 'x'\n", "[navigation.reading_time]\ndivider = 5\n"):
            with self.assertRaisesRegex(ConfigError, "неизвестные ключи"):
                self.load(text)

    def test_validation(self):
        bad = [
            '[project]\nstorage_prefix = "Go-Book"\n',
            '[project]\nversion = "1.0.0"\nversion_file = "A.md"\nversion_pattern = "x"\n',
            '[project]\nversion_file = "A.md"\n',
            '[content]\ncanonical_replacements = [["only-one"]]\n',
            '[content]\nclean_cliches = ["(unclosed"]\n',
            '[slug]\nsubsection = [1]\n',
            '[navigation.reading_time]\nmethod = "words"\n',
            '[project\n',
            '[index_page]\nstats = [{ value = "1" }]\n',
            '[index_page]\nroadmap_steps = [{ badge = "1", title_html = "t" }]\n',
            '[branding]\nlogo = "x"\n',
        ]
        for text in bad:
            with self.assertRaises(ConfigError, msg=text):
                self.load(text)

    def test_text_asset_and_fill_counts(self):
        from engine.config import read_text_asset
        from engine.template import fill_counts
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "logo.svg"), "w", encoding="utf-8") as fp:
                fp.write("<svg/>\n\n")
            cfg = BookConfig(root_dir=tmp)
            self.assertEqual(read_text_asset(cfg, "logo.svg"), "<svg/>")
            self.assertEqual(read_text_asset(cfg, ""), "")
        self.assertEqual(fill_counts("{modules} из {articles_grouped}", {"modules": 22, "articles_grouped": "1 413"}),
                         "22 из 1 413")

    def test_missing_default_file_gives_defaults(self):
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                self.assertIsInstance(load_config(), BookConfig)
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
