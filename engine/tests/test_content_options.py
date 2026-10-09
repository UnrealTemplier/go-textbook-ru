"""Тесты А2.6: выключение wikilinks, алиасы и предупреждения выносок, неоднозначные ссылки, --strict, оверлеи."""
import contextlib
import io
import os
import tempfile
import unittest

from engine.build import build, BuildError
from engine.config import (BookConfig, CalloutsConfig, ConfigError, ContentConfig, ProjectConfig,
                           _validate)
from engine.converter import MarkdownConverter
from engine.scanner import KnowledgeBaseScanner


def make_tree(root, files):
    for rel, text in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)


class ContentOptionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = os.path.join(self.tmp.name, "sources")
        make_tree(self.src, {
            "1. А/1. Введение.md": "Ссылка [[Введение]] и данные [[0 0] [1 1]].\n\n> [!critical] Важно\n> x\n\n> [!unknown]\n> y\n",
            "2. Б/1. Введение.md": "текст",
        })

    def tearDown(self):
        self.tmp.cleanup()

    def convert(self, cfg):
        sc = KnowledgeBaseScanner(self.src, cfg)
        arts = sc.scan()
        conv = MarkdownConverter(sc, cfg)
        html, _ = conv.convert_article(arts[0])
        return html, conv.warnings

    def test_defaults_warn(self):
        html, warnings = self.convert(BookConfig())
        self.assertIn('class="wikilink"', html)
        text = "\n".join(warnings)
        self.assertIn("неоднозначная ссылка [[Введение]]", text)
        self.assertIn("неизвестный тип выноски [!critical]", text)
        self.assertIn("неизвестный тип выноски [!unknown]", text)

    def test_alias_and_wikilinks_off(self):
        cfg = BookConfig(content=ContentConfig(wikilinks=False), callouts=CalloutsConfig(alias={"critical": "warning"}))
        _validate(cfg)
        html, warnings = self.convert(cfg)
        self.assertNotIn("wikilink", html)
        self.assertIn("[[0 0] [1 1]]", html)
        self.assertIn('class="callout callout-warning" aria-label="Важно"', html)
        self.assertEqual(len(warnings), 1)                      # остался только [!unknown]

    def test_strict_and_overlays(self):
        cfg = BookConfig(project=ProjectConfig(version="1.0.0"), root_dir=self.tmp.name)
        dist = os.path.join(self.tmp.name, "dist")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(build(cfg, sources_dir=self.src, dist_dir=dist))
            with self.assertRaisesRegex(BuildError, "--strict"):
                build(cfg, sources_dir=self.src, dist_dir=dist, strict=True)
            cfg.overlays = [{"title": "Трек", "modules": [1, 7]}]
            with self.assertRaisesRegex(BuildError, r"нет модулей с номерами \[7\]"):
                build(cfg, sources_dir=self.src, dist_dir=dist)

    def test_overlay_config_validation(self):
        with self.assertRaises(ConfigError):
            _validate(BookConfig(overlays=[{"title": "x", "modules": ["1"]}]))
        _validate(BookConfig(overlays=[{"title": "x", "modules": [1, 2]}]))


if __name__ == "__main__":
    unittest.main()
