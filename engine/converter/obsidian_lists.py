"""
engine/converter/obsidian_lists.py
Списки в стиле Obsidian / CommonMark для Python-Markdown (U17, анализ § 4.7.4).

Автор пишет в Obsidian: список может идти сразу за строкой абзаца, вложенный пункт сдвигается
на 2–3 пробела. Python-Markdown требует пустую строку перед списком и 4 пробела на уровень,
иначе пункты выводятся строками абзаца с «<br />» и видимым «- ». Препроцессор (приоритет 19:
после html_block = 20, поэтому строк HTML он не видит) переводит разметку:

1. Перед первым пунктом, идущим за строкой абзаца, вставляется пустая строка. Как в CommonMark,
   абзац прерывает маркированный пункт или нумерованный, начинающийся с 1.
2. Пункт уровня L получает отступ 4·L, его продолжение — 4·(L+1) плюс собственный сдвиг строки.
   Вложенность определяется по отступу маркера: пункт на 2 и более пробелов правее маркера
   родителя — дочерний.
3. Перед пунктом вставляется пустая строка, если текущий блок (от последней пустой строки)
   начался глубже этого пункта: иначе Python-Markdown склеит пункт с абзацем продолжения.
   Так же — при смене типа списка (нумерованный ↔ маркированный) на верхнем уровне: в CommonMark
   это новый список, а Python-Markdown без пустой строки склеил бы его с прошлым пунктом.
   И перед вложенным пунктом, если он идёт сразу за отдельным абзацем внутри пункта (блок
   начался строкой текста, а не пунктом).
4. Строки оград с отступом (пока препроцессор оград выключен) не трогаются; строки
   верхнеуровневых оград к этому моменту уже спрятаны fenced_code.
Эвристик для спорных мест нет (U23): такие места правятся в исходнике.
"""

import re
from typing import List

import markdown
from markdown.preprocessors import Preprocessor

from .code_mask import scan_indented_fences

ITEM_RE = re.compile(r"^(?P<ind> *)(?P<m>[-*+]|\d{1,9}[.)])(?:(?P<sp> +)(?P<rest>.*))?$")
BLOCK_START_RE = re.compile(r"^(#{1,6}\s|>|\||<|```|~~~|\x02)")


class ObsidianListPreprocessor(Preprocessor):
    def run(self, lines: List[str]) -> List[str]:
        opaque = set()
        for b in scan_indented_fences(lines):
            opaque.update(range(b["start_line"], b["end_line"] + 1))

        out: List[str] = []
        stack = []                 # открытые пункты: {"mi": отступ маркера, "ci": колонка текста, "level": L}
        prev_blank = True          # начало текста — как после пустой строки
        prev_kind = None           # "text" | "item"
        block_start = 0            # отступ (в выводе) первой строки текущего блока
        block_kind = None          # чем начался текущий блок: "text" | "item"

        def emit(line: str, starts_block: bool, kind: str):
            nonlocal block_start, block_kind
            if starts_block:
                block_start = len(line) - len(line.lstrip(" "))
                block_kind = kind
            out.append(line)

        for i, line in enumerate(lines):
            if i in opaque:
                emit(line, prev_blank, "text")
                prev_blank, prev_kind = False, "text"
                continue
            if not line.strip():
                out.append(line)
                prev_blank = True
                continue

            indent = len(line) - len(line.lstrip(" "))
            m = ITEM_RE.match(line)
            is_item = m is not None and not (not stack and indent >= 4)   # отступ 4 вне списка — блок кода
            if is_item and not stack and not prev_blank and prev_kind == "text":
                # Пункт после строки абзаца: прерывает абзац маркированный или нумерованный с 1
                marker = m.group("m")
                if marker[0].isdigit() and int(marker[:-1]) != 1:
                    is_item = False

            if is_item:
                was_in_list = bool(stack)
                sibling = None
                while stack and indent <= stack[-1]["mi"] + 1:
                    sibling = stack.pop()
                level = len(stack)
                out_indent = 4 * level
                ordered = m.group("m")[0].isdigit()
                # 1) новый список прерывает абзац; 3) возврат из блока, начатого глубже;
                # 5) смена типа списка на верхнем уровне — новый список (как в CommonMark)
                type_switch = (level == 0 and sibling is not None and sibling["level"] == 0
                               and sibling["ordered"] != ordered)
                # 4) вложенный список сразу за отдельным абзацем внутри пункта тоже прерывает абзац
                nested_after_para = level > 0 and prev_kind == "text" and block_kind == "text"
                need_blank = not prev_blank and (
                    (not was_in_list and prev_kind == "text") or block_start > out_indent
                    or type_switch or nested_after_para)
                if need_blank:
                    out.append("")
                    prev_blank = True
                marker, rest = m.group("m"), m.group("rest")
                text = " " * out_indent + marker + (" " + rest if rest is not None else "")
                emit(text, prev_blank, "item")
                sp = len(m.group("sp")) if m.group("sp") else 1
                stack.append({"mi": indent, "ci": indent + len(marker) + sp, "level": level, "ordered": ordered})
                prev_blank, prev_kind = False, "item"
                continue

            # Строка текста
            if stack:
                if prev_blank:
                    while stack and indent <= stack[-1]["mi"]:
                        stack.pop()
                elif indent < stack[-1]["ci"] and BLOCK_START_RE.match(line.lstrip(" ")):
                    stack = []          # заголовок, цитата, таблица, HTML после пункта закрывают список
            if stack:
                top = stack[-1]
                new_indent = 4 * (top["level"] + 1) + max(0, indent - top["ci"])
                emit(" " * new_indent + line.lstrip(" "), prev_blank, "text")
            else:
                emit(line, prev_blank, "text")
            prev_blank, prev_kind = False, "text"
        return out


class ObsidianListsExtension(markdown.Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(ObsidianListPreprocessor(md), "obsidian_lists", 19)
