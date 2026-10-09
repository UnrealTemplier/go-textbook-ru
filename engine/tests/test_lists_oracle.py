"""Тесты классификатора оракула А3л (engine/tools/lists_oracle.py, анализ § 6.4)."""
import unittest

from engine.tools.lists_oracle import classify_page


class ClassifyTest(unittest.TestCase):
    def test_class0_pseudo_list_became_list(self):
        old = "<p>Текст:<br />\n- a<br />\n* b</p>"
        new = "<p>Текст:</p>\n<ul>\n<li>a</li>\n<li>\n<p>b</p>\n</li>\n</ul>"
        self.assertEqual(classify_page(old, new, ""), (["0"], []))

    def test_class1_star_marker_was_italic(self):
        old = "<p>Текст:<br />\n<em> a<br />\n</em> b</p>"
        new = "<p>Текст:</p>\n<ul>\n<li>a</li>\n<li>b</li>\n</ul>"
        self.assertEqual(classify_page(old, new, "")[0], ["1"])

    def test_class2_marker_returned(self):
        old = "<ol>\n<li>a</li>\n</ol>\n<p>b</p>"
        new = "<ol>\n<li>a</li>\n<li>b</li>\n</ol>"
        self.assertEqual(classify_page(old, new, "")[0], ["2"])

    def test_class4_star_in_formula(self):
        old = "<ul>\n<li>$a <em>b$ c</em></li>\n</ul>"
        new = "<ul>\n<li>$a *b$ c</li>\n</ul>"
        self.assertEqual(classify_page(old, new, "$a *b$")[0], ["4"])

    def test_fence_and_unexplained(self):
        self.assertEqual(classify_page("<p><code>yaml x</code></p>", "<ul><li>```yaml</li></ul>", "")[0], ["fence"])
        self.assertEqual(classify_page("<p>старый текст</p>", "<p>новый текст</p>", "")[0], ["5"])


if __name__ == "__main__":
    unittest.main()
