"""
engine/tools/verify_diff.py
Сравнение двух сборок dist/ для проверки рефакторинга движка (анализ § 4.11, § 5).

Режимы:
  full     — все файлы побайтно (как diff -r): этапы А1–А2;
  article  — <article class="article-body"> каждой страницы после нормализаторов (инвариант U8);
  page     — страница целиком после нормализаторов.

Нормализаторы применяются к обеим сторонам. Страницы, перечисленные в реестре исключений
для этапа (--exceptions FILE --stage А3x), разрешены и печатаются отдельно.
Код возврата: 0 — расхождений вне исключений нет, 1 — есть.

Модуль также даёт функции проекций для оракулов этапов А3: текстовая проекция с маркерами
списков и выделения, видимый текст заголовков, блочные элементы внутри <p>,
мультимножество текстов блоков кода.
"""

import argparse
import html as html_lib
import json
import os
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from typing import Callable, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Нормализаторы
# ---------------------------------------------------------------------------
ARTICLE_RE = re.compile(r'<article class="article-body">.*?</article>', re.S)
CODE_HEADER_RE = re.compile(r'<header class="code-header">.*?</header>', re.S)
CODE_LANG_RE = re.compile(r'<span class="code-lang-tag">(.*?)</span>', re.S)
SIDEBAR_RE = re.compile(r'<aside class="app-sidebar".*?</aside>', re.S)
VENDOR_SCRIPT_RE = re.compile(r'[ \t]*<script src="[^"]*assets/vendor/[^"]*"></script>\n?')
VENDOR_CSS_RE = re.compile(r'[ \t]*<link rel="stylesheet" href="[^"]*assets/vendor/[^"]*">\n?')
ASSET_QUERY_RE = re.compile(r'(\.(?:css|js))\?v=[0-9a-f]{10}')


def whitespace_between_tags(text: str) -> str:
    """Пробельные символы между тегами не видны читателю: схлопываем их."""
    return re.sub(r">\s+<", "><", text).strip()


def code_chrome(text: str) -> str:
    """Шапка блока кода → канонический вид с одним только тегом языка; <pre><code> не трогаем."""
    def repl(m):
        lang = CODE_LANG_RE.search(m.group(0))
        return f'<header class="code-header">{lang.group(1) if lang else ""}</header>'
    return CODE_HEADER_RE.sub(repl, text)


def strip_sidebar(text: str) -> str:
    return SIDEBAR_RE.sub('<aside class="app-sidebar"></aside>', text)


def strip_conditional_scripts(text: str) -> str:
    return VENDOR_CSS_RE.sub("", VENDOR_SCRIPT_RE.sub("", text))


def strip_asset_query(text: str) -> str:
    return ASSET_QUERY_RE.sub(r"\1", text)


NORMALIZERS: Dict[str, Callable[[str], str]] = {
    "whitespace_between_tags": whitespace_between_tags,
    "code_chrome": code_chrome,
    "strip_sidebar": strip_sidebar,
    "strip_conditional_scripts": strip_conditional_scripts,
    "strip_asset_query": strip_asset_query,
}


def make_dedup_mapper(mapping_file: str) -> Callable[[str, str], str]:
    """map_dedup_ids: JSON {страница: {новый id: старый id}} применяется к новой стороне."""
    with open(mapping_file, encoding="utf-8") as fp:
        mapping = json.load(fp)

    def apply(page: str, text: str) -> str:
        for new, old in mapping.get(page, {}).items():
            text = text.replace(f'id="{new}"', f'id="{old}"').replace(f'href="#{new}"', f'href="#{old}"')
        return text
    return apply


# ---------------------------------------------------------------------------
# Реестр исключений
# ---------------------------------------------------------------------------
def load_exceptions(path: str, stage: str) -> Dict[str, str]:
    """Формат строки: этап<TAB>страница<TAB>директива<TAB>комментарий. '#' — комментарий."""
    allowed: Dict[str, str] = {}
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                raise ValueError(f"{path}: строка не в формате 'этап<TAB>страница<TAB>директива': {line!r}")
            if parts[0] == stage:
                allowed[parts[1]] = parts[2]
    return allowed


# ---------------------------------------------------------------------------
# Сравнение
# ---------------------------------------------------------------------------
def list_files(root: str) -> Set[str]:
    out = set()
    for d, _, files in os.walk(root):
        for f in files:
            out.add(os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/"))
    return out


def compare_full(old: str, new: str) -> Tuple[List[str], List[str], List[str]]:
    a, b = list_files(old), list_files(new)
    changed = []
    for rel in sorted(a & b):
        with open(os.path.join(old, rel), "rb") as fa, open(os.path.join(new, rel), "rb") as fb:
            if fa.read() != fb.read():
                changed.append(rel)
    return sorted(a - b), sorted(b - a), changed


def extract_article(text: str) -> str:
    m = ARTICLE_RE.search(text)
    return m.group(0) if m else ""


def compare_pages(old: str, new: str, mode: str, normalizers: List[str],
                  dedup: Optional[Callable[[str, str], str]] = None) -> Tuple[List[str], List[str], List[str]]:
    a = {p for p in list_files(old) if p.endswith(".html")}
    b = {p for p in list_files(new) if p.endswith(".html")}
    funcs = [NORMALIZERS[n] for n in normalizers]
    changed = []
    for rel in sorted(a & b):
        with open(os.path.join(old, rel), encoding="utf-8") as fa, open(os.path.join(new, rel), encoding="utf-8") as fb:
            ta, tb = fa.read(), fb.read()
        if mode == "article":
            ta, tb = extract_article(ta), extract_article(tb)
        if dedup:
            tb = dedup(rel, tb)
        for f in funcs:
            ta, tb = f(ta), f(tb)
        if ta != tb:
            changed.append(rel)
    return sorted(a - b), sorted(b - a), changed


# ---------------------------------------------------------------------------
# Проекции для оракулов
# ---------------------------------------------------------------------------
BLOCK_TAGS = {"div", "pre", "ul", "ol", "table", "blockquote", "aside", "figure", "p", "h1", "h2", "h3", "h4", "h5", "h6"}


class _TextProjector(HTMLParser):
    """Видимый текст с маркерами: пункты списков ('- ' / 'N. ', вложенность — TAB), <em> → '_', <strong> → '**'."""

    def __init__(self, include_pre: bool):
        super().__init__(convert_charrefs=True)
        self.include_pre = include_pre
        self.out: List[str] = []
        self.lists: List[List] = []          # [тип, счётчик]
        self.pre_depth = 0
        self.skip_depth = 0                  # script/style

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.skip_depth += 1
        elif tag == "pre":
            self.pre_depth += 1
            self.out.append("\n")
        elif tag in ("ul", "ol"):
            start = int(a.get("start") or 1)
            self.lists.append([tag, start - 1])
        elif tag == "li":
            depth = max(len(self.lists) - 1, 0)
            if self.lists and self.lists[-1][0] == "ol":
                self.lists[-1][1] += 1
                marker = f"{self.lists[-1][1]}. "
            else:
                marker = "- "
            self.out.append("\n" + "\t" * depth + marker)    # глубину отмечает TAB: пробелы схлопываются
        elif tag == "br":
            self.out.append("\n")
        elif tag in ("em", "i"):
            self.out.append("_")
        elif tag in ("strong", "b"):
            self.out.append("**")
        elif tag in BLOCK_TAGS:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip_depth -= 1
        elif tag == "pre":
            self.pre_depth -= 1
            self.out.append("\n")
        elif tag in ("ul", "ol"):
            if self.lists:
                self.lists.pop()
        elif tag in ("em", "i"):
            self.out.append("_")
        elif tag in ("strong", "b"):
            self.out.append("**")
        elif tag in BLOCK_TAGS:
            self.out.append("\n")

    def handle_data(self, data):
        if self.skip_depth or (self.pre_depth and not self.include_pre):
            return
        self.out.append(data)


def text_projection(html_text: str, include_pre: bool = False) -> str:
    p = _TextProjector(include_pre)
    p.feed(html_text)
    text = "".join(p.out)
    text = re.sub(r" +", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{2,}", "\n", text).strip()


class _HeadingCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items: List[Tuple[str, str, str, bool]] = []   # (тег, id, видимый текст, внутри <aside>)
        self.cur: Optional[List] = None
        self.aside = 0

    def handle_starttag(self, tag, attrs):
        if tag == "aside":
            self.aside += 1
        if tag in ("h2", "h3", "h4") and self.cur is None:
            self.cur = [tag, dict(attrs).get("id", ""), [], self.aside > 0]

    def handle_endtag(self, tag):
        if tag == "aside":
            self.aside -= 1
        if self.cur is not None and tag == self.cur[0]:
            self.items.append((self.cur[0], self.cur[1], "".join(self.cur[2]), self.cur[3]))
            self.cur = None

    def handle_data(self, data):
        if self.cur is not None:
            self.cur[2].append(data)


def heading_visible_texts(html_text: str) -> List[Tuple[str, str, str, bool]]:
    """Заголовки H2–H4: (тег, id, видимый текст, лежит ли внутри <aside>). Разбор — html.parser."""
    c = _HeadingCollector()
    c.feed(html_text)
    return c.items


class _BlockInP(HTMLParser):
    BLOCKS = {"div", "pre", "ul", "ol", "table", "blockquote", "aside", "figure"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.p_open = 0
        self.found: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.p_open += 1
        elif tag in self.BLOCKS and self.p_open:
            self.found.append(tag)

    def handle_endtag(self, tag):
        if tag == "p" and self.p_open:
            self.p_open -= 1


def block_in_p(html_text: str) -> List[str]:
    """Блочные элементы, открытые внутри незакрытого <p> (в исходном HTML, до починки браузером)."""
    c = _BlockInP()
    c.feed(html_text)
    return c.found


PRE_CODE_RE = re.compile(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", re.S)


def code_blocks_multiset(html_text: str) -> Counter:
    return Counter(html_lib.unescape(m.group(1)) for m in PRE_CODE_RE.finditer(html_text))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Сравнение двух сборок dist/ (инвариант контента)")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--mode", choices=["full", "article", "page"], default="full")
    ap.add_argument("--normalizers", default="", help="через запятую: " + ", ".join(NORMALIZERS))
    ap.add_argument("--dedup-map", help="JSON для map_dedup_ids")
    ap.add_argument("--exceptions", help="реестр content-exceptions.txt")
    ap.add_argument("--stage", help="этап реестра исключений, например А3а")
    ap.add_argument("--report", help="записать JSON-отчёт")
    ap.add_argument("--max-list", type=int, default=30)
    args = ap.parse_args(argv)

    names = [n for n in args.normalizers.split(",") if n]
    unknown = [n for n in names if n not in NORMALIZERS]
    if unknown:
        ap.error(f"неизвестные нормализаторы: {unknown}")

    if args.mode == "full":
        removed, added, changed = compare_full(args.old, args.new)
    else:
        dedup = make_dedup_mapper(args.dedup_map) if args.dedup_map else None
        removed, added, changed = compare_pages(args.old, args.new, args.mode, names, dedup)

    allowed = {}
    if args.exceptions:
        if not args.stage:
            ap.error("--exceptions требует --stage")
        allowed = load_exceptions(args.exceptions, args.stage)
    unexpected = [p for p in changed if p not in allowed]
    allowed_changed = [p for p in changed if p in allowed]
    allowed_unchanged = sorted(set(allowed) - set(changed))

    print(f"Режим: {args.mode}; нормализаторы: {', '.join(names) or '—'}")
    print(f"Удалено: {len(removed)}, добавлено: {len(added)}, изменено: {len(changed)} "
          f"(разрешено исключениями: {len(allowed_changed)}, вне исключений: {len(unexpected)})")
    for title, items in (("Удалённые", removed), ("Добавленные", added), ("Изменённые вне исключений", unexpected)):
        if items:
            print(f"{title}:")
            for p in items[:args.max_list]:
                print("  " + p)
            if len(items) > args.max_list:
                print(f"  … ещё {len(items) - args.max_list}")
    if allowed_unchanged:
        print(f"Внимание: {len(allowed_unchanged)} страниц из реестра исключений не изменились")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as fp:
            json.dump({"removed": removed, "added": added, "changed": changed, "unexpected": unexpected,
                       "allowed_unchanged": allowed_unchanged}, fp, ensure_ascii=False, indent=1)

    return 1 if (removed or added or unexpected) else 0


if __name__ == "__main__":
    sys.exit(main())
