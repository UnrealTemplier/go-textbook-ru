"""Книжный тест go-textbook: генератор воспроизводит закоммиченный dist/ побайтно.

Рендерит каждую страницу в памяти тем же кодом, что и сборка, и сравнивает с файлом
в dist/. Санитайзер Mermaid на всех диаграммах корпуса сверяется со снимком.
Медленный (~15 с): запускается вместе с остальными тестами, пропускается без sources/ или dist/.
"""
import hashlib
import os
import re
import unittest

from engine.scanner import KnowledgeBaseScanner
from engine.converter import MarkdownConverter
from engine.config import load_config
from engine.template import (render_article_page, render_index_page, get_book_version, set_asset_versions,
                             VERSIONED_ASSETS)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCES = os.path.join(ROOT, "sources")
DIST = os.path.join(ROOT, "dist")

# Снимок санитайзера: sha256 конкатенации очищенного кода всех диаграмм корпуса (в порядке сканирования).
MERMAID_SNAPSHOT = {"count": 2486, "sha256": "f884a34bb2aa1ac8e730aa9b2146b3b9df15e9aaf198f6cce7cf19fc5cb96cbb"}


@unittest.skipUnless(os.path.isdir(SOURCES) and os.path.isdir(DIST), "нет sources/ или dist/")
class BookCorpusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config(os.path.join(ROOT, "book.toml"))
        cls.scanner = KnowledgeBaseScanner(SOURCES, cls.config)
        cls.articles = cls.scanner.scan()
        cls.conv = MarkdownConverter(cls.scanner, cls.config)
        cls.version = get_book_version(cls.config)
        set_asset_versions(DIST, VERSIONED_ASSETS)            # ?v= — хэши ассетов закоммиченного dist/

    def test_article_pages_match_dist(self):
        mismatched = []
        for art in self.articles:
            body, toc = self.conv.convert_article(art)
            page = render_article_page(art, body, toc, self.scanner.modules_tree,
                                       total_articles=len(self.articles), version=self.version,
                                       config=self.config)
            with open(os.path.join(DIST, art.rel_output_path), encoding="utf-8") as fp:
                if fp.read() != page:
                    mismatched.append(art.rel_output_path)
        self.assertEqual(mismatched, [], f"{len(mismatched)} страниц отличаются от dist/")

    def test_index_matches_dist(self):
        page = render_index_page(self.scanner.modules_tree, len(self.articles),
                                 sum(a.mermaid_count for a in self.articles), version=self.version,
                                 config=self.config)
        with open(os.path.join(DIST, "index.html"), encoding="utf-8") as fp:
            self.assertEqual(fp.read(), page)

    def test_mermaid_sanitizer_snapshot(self):
        digest = hashlib.sha256()
        count = 0
        pattern = re.compile(r"```mermaid(.*?)```", re.DOTALL | re.IGNORECASE)
        for art in self.articles:
            with open(art.source_path, encoding="utf-8", errors="ignore") as fp:
                text = fp.read()
            for _ in pattern.finditer(text):
                count += 1
            placeholders = {}
            self.conv._extract_mermaid(text, placeholders)
            for key in sorted(placeholders, key=lambda k: int(re.search(r"\d+", k).group())):
                digest.update(placeholders[key].encode("utf-8"))
        self.assertEqual(count, MERMAID_SNAPSHOT["count"])
        if MERMAID_SNAPSHOT["sha256"] is not None:
            self.assertEqual(digest.hexdigest(), MERMAID_SNAPSHOT["sha256"])
        else:
            self.fail(f"снимок не задан: {digest.hexdigest()}")


if __name__ == "__main__":
    unittest.main()
