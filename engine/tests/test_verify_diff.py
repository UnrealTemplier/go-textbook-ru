"""Тесты инструмента сравнения сборок verify_diff.py на синтетике."""
import os
import tempfile
import unittest

from engine.tools import verify_diff as vd


PAGE = """<html><body><aside class="app-sidebar">nav {nav}</aside>
<article class="article-body">
<div class="code-block" data-lang="go">
  <header class="code-header"><span class="code-lang-tag">Go</span><button>{btn}</button></header>
  <pre class="language-go"><code class="language-go">x := 1</code></pre>
</div>
<h2 id="{hid}">Заголовок</h2>
</article>
<script src="../assets/vendor/mermaid.min.js"></script><link rel="stylesheet" href="../assets/style.css?v=0123456789">
</body></html>"""


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(text)


class CompareTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.path.join(self.tmp.name, "old")
        self.new = os.path.join(self.tmp.name, "new")

    def tearDown(self):
        self.tmp.cleanup()

    def test_full_identical_and_changed(self):
        write(self.old, "docs/a.html", PAGE.format(nav=1, btn="A", hid="h"))
        write(self.new, "docs/a.html", PAGE.format(nav=1, btn="A", hid="h"))
        self.assertEqual(vd.compare_full(self.old, self.new), ([], [], []))
        write(self.new, "docs/b.html", "x")
        write(self.new, "docs/a.html", PAGE.format(nav=2, btn="A", hid="h"))
        self.assertEqual(vd.compare_full(self.old, self.new), ([], ["docs/b.html"], ["docs/a.html"]))

    def test_article_mode_ignores_sidebar(self):
        write(self.old, "docs/a.html", PAGE.format(nav=1, btn="A", hid="h"))
        write(self.new, "docs/a.html", PAGE.format(nav=2, btn="A", hid="h"))
        self.assertEqual(vd.compare_pages(self.old, self.new, "article", [])[2], [])
        self.assertEqual(vd.compare_pages(self.old, self.new, "page", [])[2], ["docs/a.html"])
        self.assertEqual(vd.compare_pages(self.old, self.new, "page", ["strip_sidebar"])[2], [])

    def test_code_chrome(self):
        write(self.old, "docs/a.html", PAGE.format(nav=1, btn="<svg>old</svg>", hid="h"))
        write(self.new, "docs/a.html", PAGE.format(nav=1, btn="<svg><use href='#c'/></svg>", hid="h"))
        self.assertEqual(vd.compare_pages(self.old, self.new, "article", [])[2], ["docs/a.html"])
        self.assertEqual(vd.compare_pages(self.old, self.new, "article", ["code_chrome"])[2], [])

    def test_dedup_map(self):
        write(self.old, "docs/a.html", PAGE.format(nav=1, btn="A", hid="h"))
        write(self.new, "docs/a.html", PAGE.format(nav=1, btn="A", hid="h-2"))
        mp = os.path.join(self.tmp.name, "map.json")
        with open(mp, "w") as fp:
            fp.write('{"docs/a.html": {"h-2": "h"}}')
        self.assertEqual(vd.compare_pages(self.old, self.new, "article", [])[2], ["docs/a.html"])
        self.assertEqual(vd.compare_pages(self.old, self.new, "article", [], vd.make_dedup_mapper(mp))[2], [])

    def test_exceptions_and_exit_code(self):
        write(self.old, "docs/a.html", PAGE.format(nav=1, btn="A", hid="h"))
        write(self.new, "docs/a.html", PAGE.format(nav=1, btn="A", hid="x"))
        ex = os.path.join(self.tmp.name, "ex.txt")
        with open(ex, "w", encoding="utf-8") as fp:
            fp.write("# комментарий\nА3а\tdocs/a.html\tU10\tпример\n")
        self.assertEqual(vd.main([self.old, self.new, "--mode", "article"]), 1)
        self.assertEqual(vd.main([self.old, self.new, "--mode", "article", "--exceptions", ex, "--stage", "А3а"]), 0)
        self.assertEqual(vd.main([self.old, self.new, "--mode", "article", "--exceptions", ex, "--stage", "А3б"]), 1)


class NormalizerTest(unittest.TestCase):
    def test_whitespace_and_queries(self):
        self.assertEqual(vd.whitespace_between_tags("<a>\n  <b>x</b>\n</a>\n"), "<a><b>x</b></a>")
        self.assertEqual(vd.strip_asset_query('href="s.css?v=0123456789"'), 'href="s.css"')
        self.assertEqual(vd.strip_conditional_scripts('<script src="../assets/vendor/m.js"></script>\n<p>'), "<p>")


class ProjectionTest(unittest.TestCase):
    def test_text_projection_markers(self):
        html = "<p>Текст <em>курсив</em> и <strong>жир</strong></p><ul><li>a<ol><li>b</li><li>c</li></ol></li></ul><pre><code>код</code></pre>"
        self.assertEqual(vd.text_projection(html), "Текст _курсив_ и **жир**\n- a\n\t1. b\n\t2. c")
        self.assertIn("код", vd.text_projection(html, include_pre=True))

    def test_pseudo_list_visible_as_text(self):
        self.assertEqual(vd.text_projection("<p>Вот:<br />\n- один<br />\n- два</p>"), "Вот:\n- один\n- два")

    def test_headings(self):
        html = '<h2 id="a">Заголовок <code>x</code> C#</h2><aside><h3 id="b">В выноске</h3></aside><h4>&lt;pid&gt;</h4>'
        self.assertEqual(vd.heading_visible_texts(html), [
            ("h2", "a", "Заголовок x C#", False), ("h3", "b", "В выноске", True), ("h4", "", "<pid>", False)])

    def test_block_in_p(self):
        self.assertEqual(vd.block_in_p("<p>a<br /><div>b</div></p><p>c</p><div><p>d</p></div>"), ["div"])
        self.assertEqual(vd.block_in_p("<ul><li><p>a</p><pre><code>x</code></pre></li></ul>"), [])

    def test_code_multiset(self):
        c = vd.code_blocks_multiset('<pre><code class="language-go">a &lt; b</code></pre><pre class="x"><code>a &lt; b</code></pre>')
        self.assertEqual(c, {"a < b": 2})


if __name__ == "__main__":
    unittest.main()
