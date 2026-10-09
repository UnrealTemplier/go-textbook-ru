"""Тесты слоя книги: частичные шаблоны и переопределения, extra.css/js, хуки, контрольные суммы."""
import contextlib
import io
import os
import tempfile
import unittest

from engine import checksums
from engine.audit import SiteAuditor
from engine.build import build
from engine.config import load_config

BOOK_TOML = """
[project]
version = "1.0.0"
storage_prefix = "demo_"

[article_page]
footer_html = ["Подвал книги"]
"""

HOOKS = '''
def transform_markdown(text, article):
    return text + "\\n\\nДобавлено хуком."

def render_callout(c_type, title, html):
    return html.replace('class="callout ', 'class="callout hooked ')

def page_context(article, ctx):
    ctx["footer"] = ctx["footer"] + " (ctx)"

def extra_audit_checks(dist_dir):
    return ["книга: тестовая ошибка"]
'''


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(text)


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fp:
        return fp.read()


class BookLayerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        write(self.root, "book.toml", BOOK_TOML)
        write(self.root, "sources/1. Модуль/1. Статья.md", "Текст.\n\n> [!note] Заметка\n> внутри\n")

    def tearDown(self):
        self.tmp.cleanup()

    def build(self):
        cfg = load_config(os.path.join(self.root, "book.toml"))
        dist = os.path.join(self.root, "dist")
        with contextlib.redirect_stdout(io.StringIO()):
            build(cfg, dist_dir=dist, is_pilot=False)
        return cfg, dist

    def test_defaults_without_book_layer(self):
        _, dist = self.build()
        page = read(dist, "docs/01-modul/1-statya.html")
        self.assertIn("<p>Подвал книги</p>", page)
        self.assertNotIn("extra.css", page)
        self.assertNotIn("hooked", page)

    def test_template_and_asset_overrides(self):
        write(self.root, "book/overrides/templates/article_footer.html", '<footer class="app-footer">СВОЙ: ${footer}</footer>\n')
        write(self.root, "book/overrides/assets/main.js", "// свой main.js\n")
        write(self.root, "book/assets/extra.css", "body{}\n")
        write(self.root, "book/assets/extra.js", "1;\n")
        _, dist = self.build()
        page = read(dist, "docs/01-modul/1-statya.html")
        self.assertIn('<footer class="app-footer">СВОЙ: <p>Подвал книги</p></footer>', page)
        self.assertRegex(page, r'<link rel="stylesheet" href="\.\./\.\./assets/extra\.css\?v=[0-9a-f]{10}">')
        self.assertRegex(page, r'<script src="\.\./\.\./assets/extra\.js\?v=[0-9a-f]{10}"></script>')
        self.assertRegex(read(dist, "index.html"), r'<script src="\./assets/extra\.js\?v=[0-9a-f]{10}"></script>')
        self.assertEqual(read(dist, "assets/main.js"), "// свой main.js\n")
        self.assertEqual(read(dist, "assets/extra.css"), "body{}\n")

    def test_hooks(self):
        write(self.root, "book/hooks.py", HOOKS)
        cfg, dist = self.build()
        page = read(dist, "docs/01-modul/1-statya.html")
        self.assertIn("<p>Добавлено хуком.</p>", page)
        self.assertIn('class="callout hooked callout-note"', page)
        self.assertIn("<p>Подвал книги</p> (ctx)", page)
        auditor = SiteAuditor(dist, self.root, mermaid_runtime=False, config=cfg)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(auditor.run_audit())
        self.assertEqual(auditor.hook_errors, ["книга: тестовая ошибка"])


class ChecksumsTest(unittest.TestCase):
    def test_write_verify_detect_changes(self):
        with tempfile.TemporaryDirectory() as eng:
            write(eng, "a.py", "x = 1\n")
            write(eng, "sub/b.txt", "b\n")
            self.assertEqual(checksums.verify(eng), [])          # файла сумм нет — проверять нечего
            checksums.write(eng)
            self.assertEqual(checksums.verify(eng), [])
            write(eng, "a.py", "x = 2\n")
            write(eng, "new.py", "")
            os.remove(os.path.join(eng, "sub", "b.txt"))
            self.assertEqual(checksums.verify(eng), ["изменён: a.py", "удалён: sub/b.txt", "добавлен: new.py"])


if __name__ == "__main__":
    unittest.main()
