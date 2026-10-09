"""Тесты строчной маски кода (анализ § 4.7.2) на синтетике. Свойство-тест на корпусе — book/tests."""
import unittest
from collections import Counter

import markdown

from engine.code_mask import UnifiedCodeLineMask, scan_indented_fences, find_list_context


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


if __name__ == "__main__":
    unittest.main()
