"""Характеризационные тесты шагов конвертера: выноски, wikilinks, заголовки, Mermaid."""
import os
import re
import tempfile
import unittest

from engine.config import BookConfig, CalloutsConfig
from engine.scanner import KnowledgeBaseScanner
from engine.converter import MarkdownConverter


def make_tree(root, files):
    for rel, text in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)


class CalloutsTest(unittest.TestCase):
    def setUp(self):
        self.conv = MarkdownConverter(None, BookConfig(callouts=CalloutsConfig(interview_heuristic=True)))

    def render(self, text):
        return self.conv._transform_callouts(text)

    def test_known_type_and_custom_title(self):
        out = self.render("> [!warning] Осторожно <b>\n> Текст **жирный**")
        self.assertIn('<aside class="callout callout-warning" aria-label="Осторожно &lt;b&gt;">', out)
        self.assertIn('<span class="callout-icon" aria-hidden="true">⚠️</span>', out)
        self.assertIn("<p>Текст <strong>жирный</strong></p>", out)

    def test_default_title(self):
        out = self.render("> [!warning]\n> x")
        self.assertIn('aria-label="Подводные камни / Gotcha"', out)

    def test_tip_default_title_triggers_interview(self):
        # Заголовок tip по умолчанию содержит «Собеседование», поэтому срабатывает эвристика
        out = self.render("> [!tip]\n> x")
        self.assertIn('class="callout callout-interview" aria-label="Вопрос с собеседования"', out)

    def test_unknown_type_falls_back_to_note(self):
        out = self.render("> [!CRITICAL] Важное\n> x")
        self.assertIn('class="callout callout-note"', out)

    def test_interview_heuristic(self):
        out = self.render("> [!tip] Собеседование\n> вопрос")
        self.assertIn('class="callout callout-interview"', out)
        self.assertIn('aria-label="Собеседование"', out)

    def test_heuristic_off_by_default(self):
        out = MarkdownConverter(None)._transform_callouts("> [!tip] Собеседование\n> x")
        self.assertIn('class="callout callout-tip" aria-label="Собеседование"', out)

    def test_blank_line_inside_and_end(self):
        out = self.render("> [!note] A\n> one\n\n> two\n\nafter")
        self.assertEqual(out.count("<aside"), 1)
        self.assertIn("<p>one</p>\n<p>two</p>", out)
        self.assertTrue(out.rstrip().endswith("after"))

    def test_callout_at_end_of_file_and_back_to_back(self):
        out = self.render("> [!note] A\n> a\n> [!tip] B\n> b")
        self.assertEqual(out.count("<aside"), 2)


class WikilinksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        make_tree(cls.tmp.name, {
            "1. Модуль/1. Первая статья.md": "# x\n## Раздел один\n",
            "1. Модуль/2. Почему Go не похож на C#.md": "# y\n",
            "2. Другой/Подраздел/1. Глубокая.md": "# z\n",
        })
        cls.scanner = KnowledgeBaseScanner(cls.tmp.name)
        cls.articles = cls.scanner.scan()
        cls.conv = MarkdownConverter(cls.scanner)
        cls.current = cls.articles[0]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def link(self, text):
        return self.conv._transform_wikilinks(text, self.current)

    def test_paths(self):
        self.assertEqual([a.rel_output_path for a in self.articles], [
            "docs/01-modul/1-pervaya-statya.html",
            "docs/01-modul/2-pochemu-go-ne-pokhozh-na-c.html",
            "docs/02-drugoy/podrazdel/1-glubokaya.html",
        ])

    def test_resolved_with_and_without_display(self):
        self.assertEqual(self.link("[[Глубокая]]"),
                         '<a href="../02-drugoy/podrazdel/1-glubokaya.html" class="wikilink">1. Глубокая</a>')
        self.assertEqual(self.link("[[1. Глубокая|тут]]"),
                         '<a href="../02-drugoy/podrazdel/1-glubokaya.html" class="wikilink">тут</a>')

    def test_anchor_and_hash_in_title(self):
        self.assertEqual(self.link("[[Первая статья#Раздел один]]"),
                         '<a href="1-pervaya-statya.html#razdel-odin" class="wikilink">1. Первая статья</a>')
        self.assertIn('href="2-pochemu-go-ne-pokhozh-na-c.html"', self.link("[[Почему Go не похож на C#]]"))

    def test_unresolved_and_bare_anchor(self):
        self.assertEqual(self.link("[[Нет такой]]"),
                         '<span class="wikilink-unresolved" title="Заметка в разработке">Нет такой</span>')
        self.assertEqual(self.link("[[#Раздел один]]"), '<a href="#razdel-odin" class="wikilink">Раздел один</a>')


class InlineCodeWikilinksTest(WikilinksTest):
    """U20: [[…]] в inline-коде — ссылка, только если код целиком — найденная ссылка."""

    def test_found_becomes_monospace_link(self):
        self.assertEqual(self.link("см. `[[Глубокая]]`."),
                         'см. <a href="../02-drugoy/podrazdel/1-glubokaya.html" class="wikilink"><code>1. Глубокая</code></a>.')

    def test_unresolved_and_data_stay_literal(self):
        for text in ("`[[Нет такой]]`", "`map[[2]int]State`", "`[[1, 2], [3]]`"):
            self.assertEqual(self.link(text), text)

    def test_link_containing_code_is_still_a_link(self):
        out = self.link("[[Первая статья#Раздел `x`]] и `код`")
        self.assertTrue(out.startswith('<a href="1-pervaya-statya.html#razdel-x" class="wikilink">'))
        self.assertTrue(out.endswith(" и `код`"))


class HeadingsTest(unittest.TestCase):
    def setUp(self):
        self.conv = MarkdownConverter(None)

    def test_toc_and_markdown_line(self):
        text = "## Заголовок `код`\n### [Ссылка](x) и *курсив*\n#### Четвёртый"
        out, toc = self.conv._process_headings(text)
        self.assertEqual(out.splitlines()[0], "## Заголовок `код`")      # А3е: строка остаётся Markdown
        self.assertEqual(toc, [
            {"level": 2, "title": "Заголовок код", "anchor": "zagolovok-kod"},
            {"level": 3, "title": "Ссылка и курсив", "anchor": "ssylka-i-kursiv"},
            {"level": 4, "title": "Четвёртый", "anchor": "chetvyortyy"},
        ])

    def test_fences_skipped(self):
        out, toc = self.conv._process_headings("```make\n## build: x\n```\n## Настоящий")
        self.assertEqual([t["title"] for t in toc], ["Настоящий"])
        self.assertIn("## build: x", out)

    def test_trailing_hash_escaped_in_h1_h5_h6(self):
        out, _ = self.conv._process_headings("# Go против C#\n##### Пять ##\n# Закрытый #")
        self.assertEqual(out.splitlines(), ["# Go против C\\#", "##### Пять ##", "# Закрытый #"])

    def test_h1_rendered_with_hash(self):
        out, _ = self.conv._process_headings("# Go против C#")
        self.assertEqual(self.conv.md.convert(out), "<h1>Go против C#</h1>")


class MermaidTest(unittest.TestCase):
    def setUp(self):
        self.conv = MarkdownConverter(None)

    def test_class_typo_and_parens(self):
        s = self.conv._sanitize_mermaid("flowchart TD\nA[Text (x)] -->|open()| B\nclass A,succ;")
        self.assertEqual(s.splitlines(), ['flowchart TD', 'A["Text (x)"] -->|"open()"| B', 'class A succ;'])

    def test_quoted_label_untouched(self):
        line = 'A["dq[:len(dq)-1]"] --> B'
        self.assertEqual(self.conv._sanitize_mermaid("flowchart TD\n" + line).splitlines()[1], line)

    def test_extract_keeps_indent_for_mindmap(self):
        ph = {}
        out = self.conv._extract_mermaid("```mermaid\nmindmap\n  root\n    child\n```", ph)
        self.assertIn("<!--MERMAID_PLACEHOLDER_0-->", out)
        self.assertIn("mindmap\n  root\n    child", next(iter(ph.values())))


class KatexConfigTest(unittest.TestCase):
    """Конфиг KaTeX go-textbook заморожен: ошибка здесь не видна побайтной проверкой HTML."""

    def test_main_js_values(self):
        path = os.path.join(os.path.dirname(__file__), "..", "assets", "main.js")
        with open(path, encoding="utf-8") as fp:
            js = fp.read()
        # запасной конфиг main.js (для страниц без window.__BOOK__) = текущие значения go-textbook
        block = re.search(r"window\.__BOOK__\.math\) \|\| \{(.*?)\n        \};", js, re.S).group(1)
        delims = re.findall(r"\{ left: '(.*?)', right: '(.*?)', display: (true|false) \}", block)
        self.assertEqual(delims, [("$$", "$$", "true"), ("$", "$", "false"),
                                  ("\\\\(", "\\\\)", "false"), ("\\\\[", "\\\\]", "true")])
        self.assertIn("ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option']", block)
        self.assertIn("ignoredClasses: ['code-block', 'mermaid', 'mermaid-wrapper']", block)


if __name__ == "__main__":
    unittest.main()


class CodeMaskInPipelineTest(unittest.TestCase):
    """А3а: wikilinks и клише не трогают строки кода (маска единицы), вне кода — как раньше."""

    def test_wikilinks_and_cliches_skip_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_tree(tmp, {"1. М/1. Статья.md": "Как известно, [[Статья]] работает.\n\n```bash\nif [[ -f x ]]; then echo \"Как известно, да\"; fi\n```\n"})
            from engine.config import ContentConfig
            cfg = BookConfig(content=ContentConfig(clean_cliches=[r"Как известно,\s+"]))
            sc = KnowledgeBaseScanner(tmp, cfg)
            art = sc.scan()[0]
            html_out, _ = MarkdownConverter(sc, cfg).convert_article(art)
        self.assertIn('<p><a href="1-statya.html" class="wikilink">1. Статья</a> работает.</p>', html_out)
        self.assertIn("if [[ -f x ]]; then echo &quot;Как известно, да&quot;; fi", html_out)


class DedupIdsTest(unittest.TestCase):
    """А3д: повторяющиеся заголовки получают уникальные id, TOC ведёт на них."""

    def test_unique_slug_and_toc(self):
        from engine.converter import unique_slug
        used = {"shag-2"}
        self.assertEqual(unique_slug("shag", used), "shag")
        self.assertEqual(unique_slug("shag", used), "shag-3")       # shag-2 уже занят
        out, toc = MarkdownConverter(None)._process_headings("## Ответ\n## Ответ\n### Ответ")
        self.assertEqual([t["anchor"] for t in toc], ["otvet", "otvet-2", "otvet-3"])
        self.assertEqual(out, "## Ответ\n## Ответ\n### Ответ")


class HeadingsPipelineTest(unittest.TestCase):
    """А3е: разметка в H2–H4 обрабатывается, id — по TOC, хвост «#» сохраняется, у выносок id нет."""

    def test_full_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_tree(tmp, {"1. М/1. С.md": "## Анатомия `testing.B`\n## Go против PHP и C#\n## **Жирный** & <pid>\n\n> [!note] X\n> ### Внутри выноски\n"})
            sc = KnowledgeBaseScanner(tmp)
            html_out, toc = MarkdownConverter(sc).convert_article(sc.scan()[0])
        self.assertIn('<h2 id="anatomiya-testing-b">Анатомия <code>testing.B</code></h2>', html_out)
        self.assertIn('<h2 id="go-protiv-php-i-c">Go против PHP и C#</h2>', html_out)
        self.assertIn('<h2 id="zhirnyy-pid"><strong>Жирный</strong> &amp; <pid></h2>', html_out)
        self.assertIn("<h3>Внутри выноски</h3>", html_out)
        self.assertEqual([t["anchor"] for t in toc], ["anatomiya-testing-b", "go-protiv-php-i-c", "zhirnyy-pid"])
