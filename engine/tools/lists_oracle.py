"""
engine/tools/lists_oracle.py
Оракул этапа А3л (анализ § 6.4): что меняет препроцессор списков (U17) на каждой странице книги.

Статьи конвертируются в памяти дважды: с текущим book.toml и с obsidian_lists = true
(--with-fences: ещё и indented_fences = true). Для изменившихся страниц:

* тексты всех <pre><code> обязаны совпасть (Н10), иначе провал;
* сравниваются текстовые проекции verify_diff.text_projection. Псевдосписок «- a<br>» и
  настоящий <li> дают в проекции одну и ту же строку «- a», поэтому сравнение видит только
  изменения видимого текста. Перед сравнением снимаются TAB-ы вложенности, буквальный маркер
  «* »/«+ » в начале строки приравнивается к «- », а маркер свободного пункта (<li><p>),
  оторванный от текста, приклеивается обратно;
* каждое оставшееся расхождение относится к классу:
    0 — видимый текст тот же: псевдосписок стал списком;
    1 — маркер «* » раньше читался как курсив, теперь пункт (и последующие куски страницы,
        отличающиеся только выделением: сдвинутые этим курсивом пары);
    2 — вернулся пропавший маркер или номер пункта;
    3 — «_» в формуле внутри пункта перестал спариваться через строку;
    4 — «*» в формуле спаривается с «**» (Н7, до защиты $…$, U19);
    fence — ограда с отступом внутри пункта: до А3з выводится текстом, проверяется оракулом А3з;
    5 — не объяснено: дефект исходника (U23) или препроцессора. Любой класс 5 — провал.

Запуск из корня книги:
    python3 -m engine.tools.lists_oracle --book book.toml [--with-fences] [--report r.json] [--exceptions-out f.txt]
Код возврата: 0 — все страницы классифицированы и <pre><code> не изменились, 1 — нет.
"""

import argparse
import copy
import difflib
import json
import re
import sys
from collections import Counter
from typing import Dict, List, Tuple

from ..config import load_config
from ..converter import MarkdownConverter
from ..scanner import KnowledgeBaseScanner
from .verify_diff import code_blocks_multiset, text_projection

LONE_MARKER_RE = re.compile(r"(-|\d+\.)")
MARKER_RE = re.compile(r"^(- |\d+\. |_ ?)")
EMPHASIS_RE = re.compile(r"[*_]")
FORMULA_STAR_RE = re.compile(r"\$[^$\n]*\*[^$\n]*\$")


def normalize(projection: str) -> List[str]:
    out: List[str] = []
    for line in projection.split("\n"):
        line = re.sub(r"^\t+", "", line)
        line = re.sub(r"^[*+] ", "- ", line)
        if out and LONE_MARKER_RE.fullmatch(out[-1]):
            out[-1] = out[-1] + " " + line
        else:
            out.append(line)
    return out


def classify_hunk(old: List[str], new: List[str], page_has_formula_star: bool, after_star_em: bool) -> str:
    text = "\n".join(old + new)
    if "```" in text or "~~~" in text:
        return "fence"
    no_markers = lambda ls: "\n".join(MARKER_RE.sub("", l) for l in ls)
    no_emphasis = lambda ls: EMPHASIS_RE.sub("", no_markers(ls))
    if no_emphasis(old) == no_emphasis(new):
        if any(re.match(r"^_ ", l) for l in old) and any(l.startswith("- ") for l in new):
            return "1"
        if no_markers(old) == no_markers(new):
            return "2"
        if "$" in text:
            return "4" if page_has_formula_star and "*" in text else "3"
        if after_star_em:
            return "1"          # хвост того же курсива: пара «*» сдвинута до конца абзаца
    return "5"


def classify_page(old_html: str, new_html: str, source: str) -> Tuple[List[str], List[Tuple[str, List[str], List[str]]]]:
    old, new = normalize(text_projection(old_html)), normalize(text_projection(new_html))
    if old == new:
        return ["0"], []
    star = bool(FORMULA_STAR_RE.search(source))
    classes, hunks = [], []
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        cls = classify_hunk(old[i1:i2], new[j1:j2], star, "1" in classes)
        classes.append(cls)
        hunks.append((cls, old[i1:i2], new[j1:j2]))
    return sorted(set(classes)), hunks


def run(book: str, with_fences: bool) -> Dict:
    base = load_config(book)
    target = copy.deepcopy(base)
    target.markdown.obsidian_lists = True
    if with_fences:
        target.markdown.indented_fences = True
    scanner = KnowledgeBaseScanner(base.path(base.content.root), base)
    articles = scanner.scan()
    conv_old, conv_new = MarkdownConverter(scanner, base), MarkdownConverter(scanner, target)
    pages, pre_changed = {}, []
    for art in articles:
        h0, _ = conv_old.convert_article(art)
        h1, _ = conv_new.convert_article(art)
        if h0 == h1:
            continue
        if code_blocks_multiset(h0) != code_blocks_multiset(h1):
            pre_changed.append(art.rel_output_path)
        with open(art.source_path, encoding="utf-8", errors="ignore") as fp:
            classes, hunks = classify_page(h0, h1, fp.read())
        pages[art.rel_output_path] = {"classes": classes, "hunks": hunks}
    return {"pages": pages, "pre_changed": pre_changed}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Оракул А3л: классы изменений препроцессора списков")
    ap.add_argument("--book", default="book.toml")
    ap.add_argument("--with-fences", action="store_true", help="включить и препроцессор оград (А3л + А3з)")
    ap.add_argument("--report", help="JSON с классами и расхождениями по страницам")
    ap.add_argument("--exceptions-out", help="строки реестра content-exceptions.txt для этапа А3л")
    args = ap.parse_args(argv)
    result = run(args.book, args.with_fences)
    pages = result["pages"]
    count = Counter(c for p in pages.values() for c in p["classes"])
    print(f"Изменено страниц: {len(pages)}; <pre><code> изменились: {len(result['pre_changed'])}")
    print("Страниц по классам: " + ", ".join(f"{k}: {count[k]}" for k in sorted(count)))
    for path, info in sorted(pages.items()):
        if info["classes"] != ["0"]:
            print(f"  [{','.join(info['classes'])}] {path}")
    for path in result["pre_changed"]:
        print(f"  [pre] {path}")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=1)
    if args.exceptions_out:
        names = {"0": "псевдосписок стал списком", "1": "маркер «* » был курсивом", "2": "вернулся маркер или номер",
                 "3": "«_» в формуле пункта", "4": "«*» в формуле (Н7)", "fence": "ограда в пункте (А3з)"}
        with open(args.exceptions_out, "w", encoding="utf-8") as fp:
            for path, info in sorted(pages.items()):
                comment = "; ".join(names.get(c, "не объяснено") for c in info["classes"])
                fp.write(f"А3л\t{path}\tU17\t{comment}\n")
    failed = bool(result["pre_changed"]) or count.get("5", 0) > 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
