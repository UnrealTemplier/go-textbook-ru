"""Тесты проверок аудита А4 на синтетических dist/ (анализ § 4.10): без браузера."""
import contextlib
import io
import json
import os
import tempfile
import unittest

from engine.audit import SiteAuditor
from engine.config import AuditConfig, BookConfig

PAGE = """<!doctype html><html><head>
<link rel="stylesheet" href="assets/style.css?v=0123456789">{head}</head>
<body><h2 id="a">A</h2>{body}<script src="assets/main.js"></script></body></html>
"""


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(text)


class AuditChecksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.dist = os.path.join(self.root, "dist")
        write(self.dist, "assets/style.css", "body{background:url(img/bg.png)}\n")
        write(self.dist, "assets/main.js", "1;\n")
        write(self.dist, "assets/img/bg.png", "")

    def tearDown(self):
        self.tmp.cleanup()

    def audit(self, head="", body="", baseline=None, path_max=180):
        write(self.dist, "index.html", PAGE.format(head=head, body=body))
        cfg = BookConfig(audit=AuditConfig(path_max=path_max, baseline="base.json" if baseline is not None else ""),
                         root_dir=self.root)
        if baseline is not None:
            write(self.root, "base.json", json.dumps(baseline))
        a = SiteAuditor(self.dist, self.root, mermaid_runtime=False, config=cfg)
        with contextlib.redirect_stdout(io.StringIO()):
            ok = a.run_audit()
        return ok, a

    def test_clean(self):
        ok, a = self.audit(body='<a href="#a">x</a><a href="https://go.dev">внешняя ссылка допустима</a>')
        self.assertTrue(ok)

    def test_duplicate_ids_and_missing_anchor(self):
        ok, a = self.audit(body='<p id="a">x</p><a href="#нет">y</a>')
        self.assertFalse(ok)
        self.assertEqual([(i, n) for _, i, n in a.duplicate_ids], [("a", 2)])
        self.assertEqual(len(a.missing_anchors), 1)

    def test_id_in_escaped_code_is_not_an_anchor(self):
        code = "<pre><code>&lt;div id='app'&gt;&lt;/div&gt; &lt;p id=\"a\"&gt;</code></pre>"
        ok, a = self.audit(body=code + code + '<a href="#app">x</a>')
        self.assertEqual(a.duplicate_ids, [])
        self.assertEqual(len(a.missing_anchors), 1)
        ok, a = self.audit(body='<div class="x" data-k="1" id="app"></div><a href="#app">x</a>')
        self.assertTrue(ok)

    def test_missing_asset(self):
        ok, a = self.audit(head='<script src="assets/nav-data.js?v=1" defer></script>')
        self.assertFalse(ok)
        self.assertIn("nav-data.js", a.missing_assets[0][1])

    def test_offline_guard(self):
        ok, a = self.audit(head='<link rel="stylesheet" href="https://fonts.googleapis.com/css">'
                                '<style>@import url("https://cdn.example/x.css");</style>',
                           body='<img srcset="a.png 1x, //cdn.example/b.png 2x"><iframe src="http://x"></iframe>')
        self.assertFalse(ok)
        self.assertEqual(len(a.offline_issues), 4)
        write(self.dist, "assets/style.css", "@font-face{src:url(https://cdn.example/f.woff2)}\n")
        ok, a = self.audit()
        self.assertEqual(len(a.offline_issues), 1)

    def test_path_length(self):
        write(self.root, "sources/" + "д" * 30 + ".md", "")
        ok, a = self.audit(path_max=20)
        self.assertFalse(ok)
        self.assertTrue(any("длиннее 20" in d for _, d in a.filename_issues))

    def test_unresolved_wikilinks_baseline(self):
        dead = '<span class="wikilink-unresolved" title="нет">Старая</span>'
        ok, _ = self.audit(body=dead, baseline={"unresolved_wikilinks": {"index.html": ["Старая"]}})
        self.assertTrue(ok)
        ok, a = self.audit(body=dead + dead.replace("Старая", "Новая"),
                           baseline={"unresolved_wikilinks": {"index.html": ["Старая"]}})
        self.assertFalse(ok)
        self.assertEqual(len(a.baseline_issues), 2)            # новая ссылка и рост общего числа
        ok, _ = self.audit(baseline={"unresolved_wikilinks": {"index.html": ["Старая"]}})
        self.assertTrue(ok)                                    # стало меньше — не ошибка


if __name__ == "__main__":
    unittest.main()
