"""Тесты расширений Python-Markdown движка (анализ § 4.7, Приложение Б). В сборке go-textbook они выключены."""
import re
import unittest

import markdown

from engine.config import BookConfig, MarkdownConfig, MathConfig, ConfigError, _validate
from engine.converter import MarkdownConverter
from engine.converter.callouts import CalloutExtractor
from engine.converter.headings import HeadingIdsExtension, escape_trailing_hashes
from engine.converter.indented_fence import IndentedFenceExtension
from engine.converter.math_protect import MathProtectExtension
from engine.converter.obsidian_lists import ObsidianListsExtension, ObsidianListPreprocessor
from engine.tools.verify_diff import block_in_p

BASE = ["fenced_code", "tables", "sane_lists", "nl2br"]


def render(text, fences=True, lists=True, warn=None):
    ext = list(BASE)
    if fences:
        ext.append(IndentedFenceExtension(warn))
    if lists:
        ext.append(ObsidianListsExtension())
    return markdown.Markdown(extensions=ext).convert(text)


def li_of_pre(html_text):
    """Для каждого <pre>: текст ближайшего открытого <li> до первого блока (или None вне списка)."""
    out = []
    stack = []
    for m in re.finditer(r"<(/?)(li|pre)\b[^>]*>|<[^>]+>|([^<]+)", html_text):
        if m.group(2) is None and m.group(3) is None:
            continue                                   # прочие теги
        if m.group(3) is not None:
            if stack and stack[-1][1] is None:
                stack[-1][0].append(m.group(3))
            continue
        closing, tag = m.group(1), m.group(2)
        if tag == "li":
            if closing:
                stack.pop()
            else:
                stack.append([[], None])
        elif tag == "pre" and not closing:
            if stack:
                stack[-1][1] = True
            out.append("".join(stack[-1][0]).strip() if stack else None)
    return out


class IndentedFenceInputsTest(unittest.TestCase):
    """18 входов Приложения Б: 0 блоков внутри <p>, код в своём <li>, байты как у fenced_code."""

    def check(self, text, **kw):
        out = render(text, **kw)
        self.assertEqual(block_in_p(out), [], out)
        return out

    def test_01_empty_block(self):
        out = self.check("- пункт\n  ```go\n  ```\n- дальше\n  ```\n  x\n  ```")
        self.assertIn('<pre><code class="language-go"></code></pre>', out)
        self.assertIn("<pre><code>x\n</code></pre>", out)

    def test_02_closing_with_smaller_indent(self):
        out = self.check("- пункт\n    ```\n    код\n  ```\nтекст после")
        self.assertIn("<pre><code>код\n</code></pre>", out)
        self.assertNotIn("текст после\n</code>", out)

    def test_03_fence_inside_fence(self):
        out = self.check("- пример\n  ````markdown\n  ```go\n  x\n  ```\n  ````")
        self.assertIn('<pre><code class="language-markdown">```go\nx\n```\n</code></pre>', out)

    def test_04_indent_four_outside_list(self):
        out = self.check("Абзац\n\n    ```\n    x\n    ```")
        self.assertIn("<pre><code>```\nx\n```\n</code></pre>", out)

    def test_05_loose_item(self):
        out = self.check("- a\n\n  ```go\n  x\n  ```\n- b")
        self.assertEqual(out.count("<ul>"), 1)
        self.assertEqual(li_of_pre(out), ["a"])
        self.assertIn("<li>\n<p>b</p>\n</li>", out)

    def test_06_cpp(self):
        out = self.check("- код\n  ```c++\n  int x;\n  ```")
        self.assertIn('<pre><code class="language-c++">int x;\n</code></pre>', out)

    def test_07_no_language(self):
        self.assertIn("<pre><code>x\n</code></pre>", self.check("- a\n  ```\n  x\n  ```"))

    def test_08_quotes(self):
        out = self.check("- a\n  ```\n  s := \"it's\"\n  ```")
        self.assertIn("s := &quot;it's&quot;", out)

    def test_09_nested_after_text_lines(self):
        text = "- верхний\n  - вложенный\n    строка текста\n\n      ```go\n      x\n      ```"
        out = self.check(text)
        self.assertEqual(li_of_pre(out), ["вложенный\n    строка текста"])

    def test_10_other_char_or_shorter_closing(self):
        out = self.check("- a\n  ````\n  ```\n  ~~~~\n  x\n  ````")
        self.assertIn("<pre><code>```\n~~~~\nx\n</code></pre>", out)

    def test_11_longer_fence_with_inner(self):
        out = self.check("- a\n  ````\n  ```\n  ~~~\n  ````")
        self.assertIn("<pre><code>```\n~~~\n</code></pre>", out)

    def test_12_unclosed_fence_warns(self):
        warnings = []
        out = render("- a\n  ```\n  x\nтекст", warn=warnings.append)
        self.assertNotIn("<pre>", out)
        self.assertEqual(warnings, ["Unclosed fence starting at line 2"])

    def test_13_braced_language(self):
        self.assertIn('class="language-go"', self.check("- a\n  ``` { .go }\n  x\n  ```"))

    def test_14_15_same_bytes_top_level_and_in_item(self):
        top = render("```\nx\n```", fences=False, lists=False)
        item = self.check("- a\n  ```\n  x\n  ```")
        self.assertIn("<pre><code>x\n</code></pre>", top)
        self.assertIn("<pre><code>x\n</code></pre>", item)

    def test_16_text_after_code_then_next_item(self):
        text = "1. **Блочное объявление**:\n   ```go\n   var x\n   ```\n   Пояснение после кода.\n2. Следующий"
        out = self.check(text)
        self.assertEqual(li_of_pre(out), ["Блочное объявление:"])
        self.assertEqual(out.count("<ol>"), 1)
        self.assertEqual(len(re.findall(r"<li>", out)), 2)
        self.assertRegex(out, r"Пояснение после кода\.(</p>)?\s*</li>")

    def test_17_nested_item_back_to_outer(self):
        text = "1. Фаза\n   - поле\n   - Бэкенд:\n     ```go\n     type T struct{}\n     ```\n   - Релиз.\n2. Вторая"
        out = self.check(text)
        self.assertEqual(li_of_pre(out), ["Бэкенд:"])
        self.assertEqual(out.count("<ol>"), 1)
        self.assertEqual(out.count("<ul>"), 1)

    def test_18_text_and_nested_list_after_code(self):
        text = "- Пункт:\n  ```go\n  x\n  ```\n  Текст после.\n  - вложенный один\n  - вложенный два"
        out = self.check(text)
        self.assertEqual(li_of_pre(out), ["Пункт:"])
        self.assertEqual(out.count("<ul>"), 2)


class ObsidianListsTest(unittest.TestCase):
    def test_pseudo_list_after_paragraph(self):
        out = render("Текст:\n- a\n- b\n\nдальше", fences=False)
        self.assertEqual(out, "<p>Текст:</p>\n<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n<p>дальше</p>")

    def test_nesting_two_three_spaces(self):
        out = render("1. a\n   - b\n2. c\n- x\n  - y", fences=False)
        self.assertIn("<li>a<ul>\n<li>b</li>\n</ul>\n</li>", out)
        self.assertIn("<li>x<ul>\n<li>y</li>", out)

    def test_ordered_interrupts_only_from_one(self):
        self.assertEqual(render("Текст\n2. не список", fences=False), "<p>Текст<br />\n2. не список</p>")
        self.assertIn("<ol>", render("Текст\n1. список", fences=False))

    def test_star_bullet_with_bold(self):
        out = render("Текст\n* **2NF** устраняет", fences=False)
        self.assertIn("<li><strong>2NF</strong> устраняет</li>", out)

    def test_heading_closes_list_and_code_block_kept(self):
        self.assertIn("</ul>\n<h2>", render("- a\n## H", fences=False))
        self.assertIn("<pre><code>- код\n</code></pre>", render("Абзац\n\n    - код", fences=False))

    def test_quote_inside_item_interrupts_paragraph(self):
        out = render("1. **Пункт:**\n   Текст:\n   > цитата\n   > вторая строка\n2. дальше", fences=False)
        self.assertIn("<blockquote>\n<p>цитата<br />\nвторая строка</p>\n</blockquote>", out)
        self.assertNotIn("&gt;", out)
        self.assertEqual(out.count("<ol>"), 1)

    def test_pseudo_list_inside_plain_quote(self):
        out = render("> 💡 **Связанные темы:**\n> - a\n> - b\n\nдальше", fences=False)
        self.assertIn("<blockquote>\n<p>💡 <strong>Связанные темы:</strong></p>\n<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n</blockquote>", out)
        text = "> цитата\n> без списка\n>\n>  с отступом"
        self.assertEqual(ObsidianListPreprocessor(None).run(text.split("\n")), text.split("\n"))

    def test_indented_fence_lines_untouched_when_fences_off(self):
        text = "1. Конфиг:\n   ```yaml\n   - name: x\n   ```"
        out = render(text, fences=False)
        self.assertNotIn("<li>name", out)


class MathProtectTest(unittest.TestCase):
    DELIMS = MathConfig().delimiters

    def render(self, text, protect):
        return markdown.Markdown(extensions=BASE + [MathProtectExtension(self.DELIMS, protect)]).convert(text)

    def test_parens_kept(self):
        self.assertEqual(self.render(r"Закон \(L = \lambda W\)", ["\\("]), r"<p>Закон \(L = \lambda W\)</p>")
        self.assertEqual(self.render(r"\[a_1 * b_2\]", ["\\["]), r"<p>\[a_1 * b_2\]</p>")

    def test_escaping_and_code(self):
        self.assertIn(r"\(a &lt; b\)", self.render(r"\(a < b\)", ["\\("]))
        self.assertIn("<code>x</code>", self.render(r"\( a + `x` + b \)", ["\\("]))
        self.assertEqual(self.render(r"\\(не формула\\)", ["\\("]), r"<p>\(не формула\)</p>")

    def test_dollars_protected_when_asked(self):
        self.assertEqual(self.render(r"$$a_1 * b_1$$", ["$$"]), r"<p>$$a_1 * b_1$$</p>")

    def test_escaped_delimiter_does_not_close_formula(self):
        # \$ внутри формулы — знак доллара, а не конец формулы; выделение после неё остаётся
        self.assertEqual(self.render(r"$x = \$5$ и *курсив* и $y$", ["$$", "$"]),
                         r"<p>$x = \$5$ и <em>курсив</em> и $y$</p>")
        self.assertEqual(self.render(r"$$v = (\$1), (\$2)$$", ["$$"]), r"<p>$$v = (\$1), (\$2)$$</p>")
        self.assertEqual(self.render(r"\(a \\ b_1 * c_1\)", ["\\("]), r"<p>\(a \\ b_1 * c_1\)</p>")

    def test_protect_must_be_in_delimiters(self):
        with self.assertRaises(ValueError):
            MathProtectExtension([{"left": "$$", "right": "$$", "display": True}], ["\\("])


class HeadingsTest(unittest.TestCase):
    def test_escape_trailing_hashes(self):
        self.assertEqual(escape_trailing_hashes("## Go против PHP и C#"), "## Go против PHP и C\\#")
        self.assertEqual(escape_trailing_hashes("## Закрытый ##"), "## Закрытый ##")
        self.assertEqual(escape_trailing_hashes("## C\\#"), "## C\\#")

    def test_treeprocessor(self):
        md = markdown.Markdown(extensions=BASE + [HeadingIdsExtension()])
        md.heading_slugs = ["a", "b"]
        self.assertEqual(md.convert("## Один `код`\n### Два"), '<h2 id="a">Один <code>код</code></h2>\n<h3 id="b">Два</h3>')
        md.reset()
        md.heading_slugs = None
        self.assertEqual(md.convert("## Без id"), "<h2>Без id</h2>")
        md.heading_slugs = ["x"]
        with self.assertRaises(RuntimeError):
            md.convert("## Один\n## Два")


class CalloutExtractorTest(unittest.TestCase):
    def test_same_html_as_current_callouts(self):
        conv = MarkdownConverter(None)
        text = "Абзац\n\n> [!warning] Осторожно\n> Текст **жирный**\n>\n> - пункт\n\nПосле\n> [!note]\n> x"
        placeholders = {}
        out = CalloutExtractor(conv).extract_callouts(text, placeholders, None)
        self.assertIn("<!--CALLOUT_PLACEHOLDER_0-->", out)
        self.assertIn("<!--CALLOUT_PLACEHOLDER_1-->", out)
        current = conv._transform_callouts(text)
        for html_box in placeholders.values():
            self.assertIn(html_box.strip(), current)


class ConfigFlagsTest(unittest.TestCase):
    def test_fences_require_lists(self):
        with self.assertRaisesRegex(ConfigError, "obsidian_lists"):
            _validate(BookConfig(markdown=MarkdownConfig(indented_fences=True)))
        _validate(BookConfig(markdown=MarkdownConfig(indented_fences=True, obsidian_lists=True)))

    def test_protect_in_delimiters(self):
        with self.assertRaisesRegex(ConfigError, "math.protect"):
            _validate(BookConfig(math=MathConfig(protect=["\\{"])))

    def test_converter_registers_only_enabled(self):
        names = lambda conv: set(conv.md.preprocessors._data) | set(conv.md.inlinePatterns._data)
        off = names(MarkdownConverter(None))
        self.assertFalse({"indented_fence", "obsidian_lists", "math_protect_0"} & off)
        on = names(MarkdownConverter(None, BookConfig(markdown=MarkdownConfig(True, True), math=MathConfig(protect=["\\("]))))
        self.assertTrue({"indented_fence", "obsidian_lists", "math_protect_0"} <= on)


if __name__ == "__main__":
    unittest.main()
