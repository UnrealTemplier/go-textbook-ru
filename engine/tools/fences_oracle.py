"""
engine/tools/fences_oracle.py
Оракул этапа А3з (анализ § 6.4): что меняет препроцессор оград с отступом (U13) на страницах книги.

Статьи конвертируются в памяти дважды: с текущим book.toml (списки уже включены, А3л) и
с indented_fences = true. Поэтому оракул запускают до того, как флаг включён в book.toml.

Провал (код возврата 1), если хоть одно условие нарушено:
* внутри <p> есть блочный элемент (div, pre, ul, ol, table, blockquote, aside, figure) — на всех страницах;
* новый <pre> лежит вне пункта списка (в go-textbook все ограды с отступом — в пунктах);
* исчезнувший <pre> не найден целиком (непустые строки по порядку) внутри нового <pre>:
  обрывок разлитого кода обязан стать частью целого блока;
* видимый текст страницы (код включительно, без шапок блоков кода и маркеров оград, по словам)
  изменился сверх удалённого слова языка ограды — на странице, где код не был разлит.
  Разлитый код — в старом выводе вне <pre> видна обратная кавычка: ограда разобрана как
  inline-код, и её хвост ломает пары `…`, *…* и теги вокруг; там починка текста ожидаема;
* число пунктов или списков выросло на странице без разлитого кода.

Отчёт: число изменённых страниц, новых и исчезнувших <pre>, страниц с починкой текста,
<code>язык… вне <pre> (ограды, которые препроцессор не берёт: например, в обычных цитатах).

Запуск из корня книги:
    python3 -m engine.tools.fences_oracle --book book.toml [--exceptions-out f.txt]
"""

import argparse
import copy
import difflib
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from typing import Dict, List

from ..config import load_config
from ..converter import MarkdownConverter
from ..scanner import KnowledgeBaseScanner
from .verify_diff import block_in_p, code_blocks_multiset, text_projection

CODE_HEADER_RE = re.compile(r'<header class="code-header">.*?</header>', re.S)
FENCE_MARK_RE = re.compile(r"(`{3,}|~{3,})[\w#.+-]*")
LANG_INLINE_RE = re.compile(r"<code>[\w#.+-]+\n")
PRE_LANG_RE = re.compile(r'<pre[^>]*><code class="language-([^"]+)"')


class _PreInLi(HTMLParser):
    """Для каждого <pre>: (лежит ли внутри <li>, текст кода)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.li = 0
        self.cur = None
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.li += 1
        elif tag == "pre":
            self.cur = [self.li > 0, ""]

    def handle_endtag(self, tag):
        if tag == "li":
            self.li -= 1
        elif tag == "pre" and self.cur is not None:
            self.items.append(tuple(self.cur))
            self.cur = None

    def handle_data(self, data):
        if self.cur is not None:
            self.cur[1] += data


def pres_in_li(html_text: str):
    p = _PreInLi()
    p.feed(html_text)
    return p.items


def words(html_text: str) -> List[str]:
    text = text_projection(CODE_HEADER_RE.sub("", html_text), include_pre=True)
    return FENCE_MARK_RE.sub(" ", text).split()


def lines_of(code: str) -> List[str]:
    return [l.strip() for l in code.split("\n") if l.strip()]


def contained(part: List[str], whole: List[str]) -> bool:
    """Строки part идут в whole по порядку (не обязательно подряд)."""
    it = iter(whole)
    return all(any(l == w for w in it) for l in part)


def check_page(h0: str, h1: str) -> Dict:
    problems, repairs = [], 0
    m0, m1 = code_blocks_multiset(h0), code_blocks_multiset(h1)
    gone, added = m0 - m1, m1 - m0
    added_codes = [lines_of(c) for c in added]
    for code in gone:
        if not any(contained(lines_of(code), whole) for whole in added_codes):
            problems.append("исчезнувший <pre> не найден в новых: " + code[:60].replace("\n", "⏎"))
    outside = Counter(code for in_li, code in pres_in_li(h1) if not in_li)
    for code in added:
        if outside[code] > Counter(c for in_li, c in pres_in_li(h0) if not in_li)[code]:
            problems.append("новый <pre> вне пункта: " + code[:60].replace("\n", "⏎"))
    spilled = "`" in text_projection(h0)
    langs = set(PRE_LANG_RE.findall(h1))
    a, b = words(h0), words(h1)
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal" or (op == "delete" and i2 - i1 == 1 and a[i1] in langs):
            continue
        if spilled:
            repairs += 1
        else:
            problems.append(f"текст изменился: {' '.join(a[i1:i2])[:60]} → {' '.join(b[j1:j2])[:60]}")
    li0, li1 = len(re.findall(r"<li[ >]", h0)), len(re.findall(r"<li[ >]", h1))
    lists0 = h0.count("<ul>") + len(re.findall(r"<ol[ >]", h0))
    lists1 = h1.count("<ul>") + len(re.findall(r"<ol[ >]", h1))
    if (li1 > li0 or lists1 > lists0) and not spilled:
        problems.append(f"пунктов {li0} → {li1}, списков {lists0} → {lists1} без разлитого кода")
    return {"added": sum(added.values()), "gone": sum(gone.values()), "repairs": repairs,
            "li": (li0, li1), "spilled": spilled, "problems": problems}


def run(book: str) -> Dict:
    base = load_config(book)
    target = copy.deepcopy(base)
    target.markdown.indented_fences = True
    scanner = KnowledgeBaseScanner(base.path(base.content.root), base)
    articles = scanner.scan()
    conv_old, conv_new = MarkdownConverter(scanner, base), MarkdownConverter(scanner, target)
    pages, block_problems, lang_inline = {}, [], 0
    for art in articles:
        h0, _ = conv_old.convert_article(art)
        h1, _ = conv_new.convert_article(art)
        found = block_in_p(h1)
        if found:
            block_problems.append(f"{art.rel_output_path}: внутри <p> {', '.join(found)}")
        lang_inline += len(LANG_INLINE_RE.findall(h1))
        if h0 != h1:
            pages[art.rel_output_path] = check_page(h0, h1)
    return {"pages": pages, "block_in_p": block_problems, "lang_inline": lang_inline}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Оракул А3з: ограды с отступом в пунктах списков")
    ap.add_argument("--book", default="book.toml")
    ap.add_argument("--exceptions-out", help="строки реестра content-exceptions.txt для этапа А3з")
    args = ap.parse_args(argv)
    result = run(args.book)
    pages = result["pages"]
    added = sum(p["added"] for p in pages.values())
    gone = sum(p["gone"] for p in pages.values())
    repaired = [path for path, p in pages.items() if p["repairs"]]
    print(f"Изменено страниц: {len(pages)}; новых <pre>: {added}; исчезнувших <pre>: {gone}")
    print(f"Блоков внутри <p>: {len(result['block_in_p'])}; <code>язык… вне <pre>: {result['lang_inline']}")
    print(f"Страниц с разлитым кодом, где текст починился: {len(repaired)}")
    for path in sorted(repaired):
        p = pages[path]
        print(f"  {path}: правок {p['repairs']}, пунктов {p['li'][0]} → {p['li'][1]}")
    problems = list(result["block_in_p"])
    for path, p in sorted(pages.items()):
        problems += [f"{path}: {msg}" for msg in p["problems"]]
    for msg in problems:
        print("ПРОВАЛ " + msg)
    if args.exceptions_out:
        with open(args.exceptions_out, "w", encoding="utf-8") as fp:
            for path, p in sorted(pages.items()):
                comment = f"ограды в пунктах → <pre>: {p['added']}"
                if p["repairs"]:
                    comment += "; починен текст вокруг разлитого кода"
                fp.write(f"А3з\t{path}\tU13\t{comment}\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
