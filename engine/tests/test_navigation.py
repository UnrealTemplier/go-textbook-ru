"""Тесты гибридного сайдбара (А3б): nav-data.js и вывод сайдбара в режимах static и hybrid."""
import json
import os
import re
import tempfile
import unittest

from engine.build import generate_nav_data_js
from engine.config import BookConfig
from engine.scanner import KnowledgeBaseScanner
from engine.template import render_sidebar


def make_tree(root, files):
    for rel, text in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)


class NavigationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        make_tree(self.tmp.name, {
            "1. Первый/1. А.md": "", "1. Первый/2. Б.md": "",
            "2. Второй/Раздел/1. В <тег>.md": "", "2. Второй/Раздел/2. Г.md": "",
        })
        self.sc = KnowledgeBaseScanner(self.tmp.name, BookConfig())
        self.arts = self.sc.scan()

    def tearDown(self):
        self.tmp.cleanup()

    def test_nav_data(self):
        dist = os.path.join(self.tmp.name, "dist")
        generate_nav_data_js(self.sc.modules_tree, self.sc.content_count, dist)
        with open(os.path.join(dist, "assets", "nav-data.js"), encoding="utf-8") as fp:
            text = fp.read()
        self.assertTrue(text.startswith("window.NAV_DATA = ") and text.endswith(";\n"))
        data = json.loads(text[len("window.NAV_DATA = "):-2])
        self.assertEqual(data["count"], 4)
        self.assertEqual(data["modules"][0]["items"], [["1. А", "docs/01-pervyy/1-a.html"], ["2. Б", "docs/01-pervyy/2-b.html"]])
        self.assertEqual(data["modules"][1]["subs"][0]["name"], "Раздел")
        self.assertEqual(data["modules"][1]["subs"][0]["items"][0][0], "1. В <тег>")

    def test_static_mode_lists_everything(self):
        html = render_sidebar(self.sc.modules_tree, self.arts[0], "../../")
        self.assertEqual(html.count('class="nav-item'), 4)
        self.assertNotIn("data-nav", html)

    def test_hybrid_mode(self):
        html = render_sidebar(self.sc.modules_tree, self.arts[0], "../../", hybrid=True)
        self.assertIn('<details class="nav-module active-module" open data-nav-module="1">', html)
        self.assertIn('<details class="nav-module" data-nav-module="2">', html)
        self.assertIn('<div class="nav-module-content" data-nav-stub="1">', html)
        self.assertIn('<li class="nav-item"><a href="../../docs/02-vtoroy/razdel/1-v-teg.html">1. В &lt;тег&gt;</a></li>', html)
        self.assertEqual(html.count('class="nav-item'), 3)          # 2 текущего модуля + ссылка-заглушка
        none = render_sidebar(self.sc.modules_tree, self.arts[0], "../../", hybrid=True, static_module_list=False)
        self.assertNotIn('data-nav-module="2"', none)


if __name__ == "__main__":
    unittest.main()
