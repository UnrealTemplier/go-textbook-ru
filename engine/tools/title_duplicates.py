"""
engine/tools/title_duplicates.py
Реестр двойных H1 (U14, анализ § 6.4): статьи, где первый «# …» в тексте повторяет заголовок
страницы не дословно, а с расширенным текстом. Точные копии движок убирает из тела сам
(scanner.duplicate_h1), а такие пары остаются оба и сводятся вручную в фактчеке.

Запуск из корня книги:
    python3 -m engine.tools.title_duplicates --book book.toml --out fact-checks/title-duplicates.md
    python3 -m engine.tools.title_duplicates --book book.toml --out fact-checks/title-duplicates.md --check

--check не пишет файл, а сверяет его с текущими sources/: код возврата 1, если реестр устарел.
Применимо только при title_source = "filename": при "h1" заголовок страницы и есть H1.
"""

import argparse
import os
import sys
from typing import List, Tuple

from ..config import load_config
from ..scanner import KnowledgeBaseScanner, find_first_h1


def collect(config) -> Tuple[List[Tuple[str, str, str]], int]:
    """(пары «путь в sources/, заголовок страницы, H1 из текста», число точных копий)."""
    sources = config.path(config.content.root)
    articles = KnowledgeBaseScanner(sources, config).scan()
    pairs, exact = [], 0
    for art in articles:
        with open(art.source_path, encoding="utf-8", errors="ignore") as fp:
            h1 = find_first_h1(fp.read())
        if h1 is None:
            continue
        if h1[1] == art.title:
            exact += 1
        else:
            pairs.append((os.path.relpath(art.source_path, sources).replace(os.sep, "/"), art.title, h1[1]))
    return pairs, exact


def cell(text: str) -> str:
    return text.replace("|", "\\|")


def render(pairs: List[Tuple[str, str, str]], exact: int) -> str:
    lines = [
        "# Реестр двойных H1",
        "",
        "> Сгенерировано `python3 -m engine.tools.title_duplicates`; вручную не править.",
        "",
        "В статье два заголовка первого уровня: заголовок страницы (из имени файла, его рисует шаблон) "
        "и первый «# …» в тексте. Точные копии движок убирает из тела сам (U14, точных копий сейчас: "
        f"{exact}). Ниже — {len(pairs)} пар, где H1 в тексте отличается: на странице видны оба. "
        "При сведении в фактчеке нельзя терять информацию ни из одного заголовка: уточнения из H1 "
        "переносятся в имя файла или в текст, после чего H1 удаляется из исходника.",
        "",
        "| № | Статья (`sources/`) | Заголовок страницы | H1 в тексте |",
        "|--:|---|---|---|",
    ]
    for i, (path, title, h1) in enumerate(pairs, 1):
        lines.append(f"| {i} | `{cell(path)}` | {cell(title)} | {cell(h1)} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Реестр двойных H1 (U14)")
    ap.add_argument("--book", default="book.toml")
    ap.add_argument("--out", required=True)
    ap.add_argument("--check", action="store_true", help="сверить реестр с sources/, не записывая")
    args = ap.parse_args(argv)
    config = load_config(args.book)
    if config.content.title_source != "filename":
        print("title_source = \"h1\": двойных H1 не бывает, реестр не нужен", file=sys.stderr)
        return 2
    pairs, exact = collect(config)
    text = render(pairs, exact)
    if args.check:
        try:
            with open(args.out, encoding="utf-8") as fp:
                current = fp.read()
        except FileNotFoundError:
            current = None
        if current != text:
            print(f"{args.out} устарел: перегенерируйте без --check", file=sys.stderr)
            return 1
        print(f"{args.out} актуален: {len(pairs)} пар, точных копий {exact}")
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fp:
        fp.write(text)
    print(f"{args.out}: {len(pairs)} пар, точных копий {exact}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
