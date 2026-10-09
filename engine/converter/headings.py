"""
engine/converter/headings.py
Разметка в заголовках H2–H4 (U24, анализ § 4.7.6, Приложение А.4) и хвост «#» (Е1).

Сейчас _process_headings выводит H2–H4 сырым HTML до Python-Markdown, и разметка в них не
обрабатывается. С коммита А3е строка заголовка остаётся Markdown, а id ставит этот
treeprocessor (приоритет 5) по списку якорей TOC — только в основном вызове статьи.
"""

import re

import markdown
from markdown.treeprocessors import Treeprocessor

# Хвост «#», приклеенный к слову (не к пробелу, «\» или другому «#»): «C#» → «C\#».
TRAILING_HASH_RE = re.compile(r"^(#{1,6}\s+.*[^\s#\\])(#+)\s*$")


def escape_trailing_hashes(line: str) -> str:
    """Python-Markdown срезает «#» в конце заголовка как закрывающую последовательность."""
    return TRAILING_HASH_RE.sub(lambda m: m.group(1) + "\\#" * len(m.group(2)), line)


class HeadingTreeprocessor(Treeprocessor):
    def run(self, root):
        slugs = getattr(self.md, "heading_slugs", None)
        if slugs is None:              # тело выноски или другой вспомогательный вызов
            return
        headings = [el for el in root.iter() if el.tag in ("h2", "h3", "h4")]
        if len(headings) != len(slugs):
            raise RuntimeError(f"HeadingTreeprocessor: {len(headings)} заголовков в дереве, "
                               f"{len(slugs)} в TOC")
        for h, slug in zip(headings, slugs):
            h.set("id", slug)


class HeadingIdsExtension(markdown.Extension):
    def extendMarkdown(self, md):
        md.heading_slugs = None
        md.treeprocessors.register(HeadingTreeprocessor(md), "heading_ids", 5)
