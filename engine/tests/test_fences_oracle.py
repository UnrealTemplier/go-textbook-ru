"""Тесты проверок оракула А3з (engine/tools/fences_oracle.py, анализ § 6.4)."""
import unittest

from engine.tools.fences_oracle import check_page, contained

OLD = "<ol>\n<li>Конфиг:<br />\n<code>yaml\na: 1</code></li>\n</ol>"
NEW = ('<ol>\n<li>\n<p>Конфиг:</p>\n<div class="code-block"><header class="code-header"><span>YAML</span></header>\n'
       '<pre class="language-yaml"><code class="language-yaml">a: 1\n</code></pre></div>\n</li>\n</ol>')


class FencesOracleTest(unittest.TestCase):
    def test_fence_in_item_passes(self):
        res = check_page(OLD, NEW)
        self.assertEqual((res["added"], res["gone"], res["problems"]), (1, 0, []))

    def test_pre_outside_item_fails(self):
        new = NEW.replace("<ol>\n<li>\n", "").replace("</li>\n</ol>", "")
        self.assertTrue(any("вне пункта" in p for p in check_page(OLD, new)["problems"]))

    def test_text_change_without_spilled_code_fails(self):
        new = NEW.replace("Конфиг:", "Другое:")
        self.assertTrue(any("текст изменился" in p for p in check_page(OLD, new)["problems"]))

    def test_fragment_must_be_inside_new_block(self):
        self.assertTrue(contained(["b", "d"], ["a", "b", "c", "d"]))
        self.assertFalse(contained(["d", "b"], ["a", "b", "c", "d"]))
        old = OLD + "\n<pre><code>потерянный обрывок\n</code></pre>"
        self.assertTrue(any("не найден" in p for p in check_page(old, NEW)["problems"]))


if __name__ == "__main__":
    unittest.main()
