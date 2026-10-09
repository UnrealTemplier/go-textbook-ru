"""Тесты строчной маски кода (анализ § 4.7.2): синтетика и свойство-тест на корпусе go-textbook."""
import os
import re
import unittest
from collections import Counter

import markdown

from builder.code_mask import UnifiedCodeLineMask, scan_indented_fences, find_list_context
from builder.converter import MarkdownConverter
from builder.scanner import KnowledgeBaseScanner
from builder.tools.verify_diff import code_blocks_multiset

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCES = os.path.join(ROOT, "sources")


def new_md():
    return markdown.Markdown(extensions=["fenced_code", "tables", "sane_lists", "nl2br"])


def mask_code_multiset(text, md, include_indented):
    """Тексты блоков, найденных маской, в том виде, в каком их выводит Python-Markdown."""
    mask = UnifiedCodeLineMask(text, md, include_indented)
    norm = md.preprocessors['normalize_whitespace'].run(text.split('\n'))
    out = Counter()
    indented = {b['start_line']: b for b in scan_indented_fences(norm)} if include_indented else {}
    for first, last in mask.blocks:
        if first in indented:
            body = indented[first]['code_lines']
        else:
            body = norm[first + 1:last]
        out["\n".join(body) + "\n" if body else ""] += 1
    return mask, out


class SyntheticTest(unittest.TestCase):
    def test_top_level_fences(self):
        text = "текст\n```go\nx := 1\n```\nещё\n~~~~\na\n```\nb\n~~~~\nконец"
        mask = UnifiedCodeLineMask(text, new_md(), False)
        self.assertEqual(mask.blocks, [(1, 3), (5, 9)])
        self.assertFalse(mask.is_line_in_code(0))
        self.assertTrue(mask.is_line_in_code(7))

    def test_tab_and_trailing_spaces_do_not_shift_lines(self):
        text = "\tтаб\n   \n```\ncode\n```\n"
        self.assertEqual(UnifiedCodeLineMask(text, new_md(), False).blocks, [(2, 4)])

    def test_indented_fence_in_list_only_when_enabled(self):
        text = "1. Пункт:\n   ```go\n   x\n   ```\n2. Дальше"
        self.assertEqual(UnifiedCodeLineMask(text, new_md(), False).blocks, [])
        self.assertEqual(UnifiedCodeLineMask(text, new_md(), True).blocks, [(1, 3)])

    def test_list_context_through_text_lines(self):
        lines = ["- пункт", "  текст пункта", "", "  ещё текст", "  ```", "  x", "  ```"]
        self.assertEqual(find_list_context(lines, 4, 2), (True, 0))    # подъём через строки текста до маркера
        lines = ["- пункт", "  текст", "", "      ```go", "      x", "      ```"]
        self.assertEqual(find_list_context(lines, 3, 6), (True, 2))
        self.assertEqual(find_list_context(["абзац", "  ```"], 1, 2), (False, 0))

    def test_closing_fence_rules(self):
        lines = ["- a", "  ````", "  ```", "  ~~~", "  ````"]
        self.assertEqual([(b['start_line'], b['end_line'], b['code_lines']) for b in scan_indented_fences(lines)],
                         [(1, 4, ["```", "~~~"])])

    def test_unclosed_fence_warns(self):
        warnings = []
        self.assertEqual(scan_indented_fences(["- a", "  ```", "  x", "текст"], warnings.append), [])
        self.assertEqual(warnings, ["Unclosed fence starting at line 2"])

    def test_indent_four_outside_list_is_plain_code(self):
        self.assertEqual(scan_indented_fences(["абзац", "", "    ```", "    x", "    ```"]), [])


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
            raw = open(art.source_path, encoding="utf-8", errors="ignore").read()
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
