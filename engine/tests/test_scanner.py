"""Тесты рекурсивного сканера: ошибки структуры, пути, индексные файлы и title_source = "h1"."""
import contextlib
import io
import os
import re
import tempfile
import unittest

from engine.build import build
from engine.config import BookConfig, ContentConfig, ProjectConfig
from engine.converter import MarkdownConverter
from engine.scanner import KnowledgeBaseScanner, ScanError
from engine.template import render_article_page


def make_tree(root, files):
    for rel, text in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)


class StructureErrorsTest(unittest.TestCase):
    def scan(self, files, config=None):
        with tempfile.TemporaryDirectory() as tmp:
            make_tree(tmp, files)
            return KnowledgeBaseScanner(tmp, config).scan()

    def test_md_in_root(self):
        with self.assertRaisesRegex(ScanError, "в корне"):
            self.scan({"x.md": "", "1. М/a.md": ""})

    def test_module_without_number_and_duplicate_number(self):
        with self.assertRaisesRegex(ScanError, "без номера"):
            self.scan({"Модуль/a.md": ""})
        with self.assertRaisesRegex(ScanError, "два модуля с номером 1"):
            self.scan({"1. А/a.md": "", "01. Б/b.md": ""})

    def test_files_next_to_subdirs_below_module(self):
        with self.assertRaisesRegex(ScanError, "рядом с подкаталогами"):
            self.scan({"1. М/Раздел/a.md": "", "1. М/Раздел/Глубже/b.md": ""})

    def test_index_file_next_to_subdirs_is_allowed(self):
        cfg = BookConfig(content=ContentConfig(index_file=r"^0+\. "))
        arts = self.scan({"1. М/Раздел/00. О разделе.md": "", "1. М/Раздел/Глубже/b.md": ""}, cfg)
        self.assertEqual([a.is_index for a in arts], [True, False])

    def test_output_path_collision(self):
        long = "Очень длинное название статьи про устройство памяти и кэшей процессора"
        with self.assertRaisesRegex(ScanError, "совпадение выходных путей"):
            self.scan({f"1. М/{long} часть один.md": "", f"1. М/{long} часть два.md": ""})

    def test_h1_required(self):
        with self.assertRaisesRegex(ScanError, "нет заголовка"):
            self.scan({"1. М/a.md": "текст"}, BookConfig(content=ContentConfig(title_source="h1")))


class PathsTest(unittest.TestCase):
    def test_levels_and_flattened_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_tree(tmp, {
                "1. Модуль/1. В корне.md": "",
                "1. Модуль/Раздел/1. Статья.md": "",
                "1. Модуль/Большой раздел/Часть/1. Глубокая.md": "",
                "1. Модуль/Большой раздел/Ветка/Ещё глубже/1. Самая.md": "",
            })
            sc = KnowledgeBaseScanner(tmp)
            arts = sc.scan()
            self.assertEqual([a.rel_output_path for a in arts], [
                "docs/01-modul/1-v-korne.html",
                "docs/01-modul/bolshoy-razdel/vetka/eshchyo-glubzhe/1-samaya.html",
                "docs/01-modul/bolshoy-razdel/chast/1-glubokaya.html",
                "docs/01-modul/razdel/1-statya.html",
            ])
            names = [s["name"] for s in sc.modules_tree[0]["subsections"]]
            self.assertEqual(names, ["Большой раздел / Ветка / Ещё глубже", "Большой раздел / Часть", "Раздел"])
            self.assertEqual(sc.content_count, 4)
            self.assertFalse(sc.has_index_pages)


class IndexBookTest(unittest.TestCase):
    """Книга по образцу go-workout: глава / раздел / задача, индексные файлы, заголовки из H1."""

    FILES = {
        "001. Глава/000. О главе.md": "# Глава первая: полное название\n\nОписание главы.\n",
        "001. Глава/01. Раздел/00. О разделе.md": "# Раздел про горутины, длинное название\n",
        "001. Глава/01. Раздел/001. Первая.md": "# Первая задача\n\n## Условие\nТекст.\n",
        "001. Глава/01. Раздел/002. Вторая.md": "# Вторая задача\n\n## Условие\nТекст.\n",
        "002. Другая/000. О главе.md": "# Глава вторая\n",
        "002. Другая/01. Раздел/001. Третья.md": "# Третья задача\n",
    }

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        make_tree(self.tmp.name, self.FILES)
        self.cfg = BookConfig(project=ProjectConfig(version="1.0.0"),
                              content=ContentConfig(title_source="h1", index_file=r"^0+\. "),
                              root_dir=self.tmp.name)
        self.sc = KnowledgeBaseScanner(self.tmp.name, self.cfg)
        self.arts = self.sc.scan()

    def tearDown(self):
        self.tmp.cleanup()

    def test_order_titles_and_counts(self):
        self.assertEqual([(a.title, a.is_index, a.position) for a in self.arts], [
            ("Глава первая: полное название", True, 0),
            ("Раздел про горутины, длинное название", True, 0),
            ("Первая задача", False, 1),
            ("Вторая задача", False, 2),
            ("Глава вторая", True, 0),
            ("Третья задача", False, 3),
        ])
        self.assertEqual(self.sc.content_count, 3)
        self.assertTrue(self.sc.has_index_pages)
        self.assertIs(self.arts[2].prev_article, self.arts[1])          # пагинация идёт через заглавные
        self.assertIs(self.arts[2].module_index, self.arts[0])
        self.assertIs(self.arts[2].section_index, self.arts[1])
        self.assertIsNone(self.arts[5].section_index)

    def render(self, art):
        conv = MarkdownConverter(self.sc, self.cfg)
        body, toc = conv.convert_article(art)
        return body, render_article_page(art, body, toc, self.sc.modules_tree, total_articles=self.sc.content_count,
                                         version="1.0.0", config=self.cfg, show_position=True)

    def test_task_page(self):
        body, page = self.render(self.arts[3])
        self.assertNotIn("<h1>Вторая задача</h1>", body)                 # H1 убран из тела
        self.assertIn('<h1 class="article-title">Вторая задача</h1>', page)
        self.assertIn('<span class="meta-tag position-tag">2 из 3</span>', page)
        self.assertIn('<li class="crumb-item crumb-module"><a href="../../../docs/01-glava/000-o-glave.html" class="crumb-link">Глава</a></li>', page)
        self.assertIn('class="crumb-link">01. Раздел</a>', page)          # крошка раздела — ссылка
        self.assertIn('class="index-link">01. Раздел</a>', page)          # и узел раздела в сайдбаре

    def test_index_page(self):
        _, page = self.render(self.arts[0])
        self.assertNotIn("position-tag", page)
        children = re.search(r'<ul class="index-children">(.*?)</ul>', page, re.S).group(1)
        self.assertIn(">Раздел про горутины, длинное название</a>", children)
        _, page = self.render(self.arts[1])
        children = re.search(r'<ul class="index-children">(.*?)</ul>', page, re.S).group(1)
        self.assertEqual(re.findall(r">([^<]+)</a>", children), ["Первая задача", "Вторая задача"])

    def test_full_build(self):
        dist = os.path.join(self.tmp.name, "dist")
        with contextlib.redirect_stdout(io.StringIO()):
            build(self.cfg, sources_dir=self.tmp.name, dist_dir=dist, is_pilot=False)
        self.assertTrue(os.path.exists(os.path.join(dist, "docs/01-glava/01-razdel/002-vtoraya.html")))
        with open(os.path.join(dist, "index.html"), encoding="utf-8") as fp:
            index = fp.read()
        self.assertIn("2 статей", index)


if __name__ == "__main__":
    unittest.main()
