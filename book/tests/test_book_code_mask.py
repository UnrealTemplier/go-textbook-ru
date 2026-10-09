"""Книжный свойство-тест маски кода на корпусе go-textbook (анализ § 4.7.2)."""
import os
import unittest

from engine.converter import MarkdownConverter
from engine.scanner import KnowledgeBaseScanner
from engine.tools.verify_diff import code_blocks_multiset
from engine.tests.test_code_mask import new_md, mask_code_multiset

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCES = os.path.join(ROOT, "sources")


@unittest.skipUnless(os.path.isdir(SOURCES), "нет sources/")
class CorpusPropertyTest(unittest.TestCase):
    """Блоки маски = блоки кода, которые Python-Markdown выводит для той же единицы.

    Конфигурация до А3з: include_indented=False. Единицы: текст статьи на шаге 4 (после клише,
    Mermaid и выносок) и тело каждой выноски.
    """
    # Блок с отступом 4 без оград: маска его не видит (известное ограничение, анализ § 4.7.2)
    KNOWN_LIMITATION = {"article": {"6. Deadlock и их предотвращение.md"}}   # модуль 12

    @classmethod
    def setUpClass(cls):
        cls.scanner = KnowledgeBaseScanner(SOURCES)
        cls.articles = cls.scanner.scan()

    def test_articles_and_callout_bodies(self):
        conv = MarkdownConverter(self.scanner)
        bodies = []
        original = conv._render_callout_block

        def record(callout_type, title, body_lines):
            bodies.append("\n".join(body_lines))
            return original(callout_type, title, body_lines)
        conv._render_callout_block = record

        md = new_md()
        bad_articles, bad_bodies = [], []
        for art in self.articles:
            with open(art.source_path, encoding="utf-8", errors="ignore") as fp:
                raw = fp.read()
            text = conv._clean_cliches(raw)
            text = conv._extract_mermaid(text, {})
            before = len(bodies)
            text = conv._transform_callouts(text)
            # блоки кода, уже вставленные в текст как HTML выносок, Python-Markdown пропустит как есть
            raw_html_code = code_blocks_multiset(text)
            md.reset()
            produced = code_blocks_multiset(md.convert(text)) - raw_html_code
            md.reset()
            _, masked = mask_code_multiset(text, md, False)
            if produced != masked:
                bad_articles.append(os.path.basename(art.source_path))
            for body in bodies[before:]:
                md.reset()
                body_produced = code_blocks_multiset(md.convert(body))
                md.reset()
                _, body_masked = mask_code_multiset(body, md, False)
                if body_produced != body_masked:
                    bad_bodies.append(os.path.basename(art.source_path))
        self.assertEqual(set(bad_articles), self.KNOWN_LIMITATION["article"])
        self.assertEqual(bad_bodies, [])
        self.assertGreater(len(bodies), 4000)


if __name__ == "__main__":
    unittest.main()
