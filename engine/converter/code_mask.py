"""
engine/converter/code_mask.py
Строчная маска кода (анализ § 4.7.1–4.7.2, Приложение А.1).

Маска — номера строк текста единицы конвертации (статьи или тела выноски), которые
Python-Markdown выведет кодом. Её используют шаги, правящие текст (клише, wikilinks),
чтобы не трогать код. Сканер оград с отступом — один для маски и для препроцессора оград.

Известное ограничение: блоки кода с отступом 4 без оград маска не видит.
"""

import re
from bisect import bisect_right
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import markdown
from markdown.extensions.fenced_code import FencedBlockPreprocessor

LIST_MARKER_RE = re.compile(r'^(?:[-*+]|\d+\.)\s+')
OPEN_FENCE_RE = re.compile(
    r'^(?P<indent>[ \t]+)(?P<fence>`{3,}|~{3,})[ ]*(?:\{?[. ]*(?P<lang>[\w#.+-]*)[ ]*\}?)?[ ]*$')
CLOSE_FENCE_RE = re.compile(r'^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})[ ]*$')


def find_list_context(lines: List[str], fence_idx: int, fence_indent_len: int) -> Tuple[bool, int]:
    """Вверх до первой непустой строки с отступом меньше, чем у ограды; затем — до маркера списка."""
    k = fence_idx - 1
    while k >= 0:
        line = lines[k]
        if not line.strip():
            k -= 1
            continue
        cur_indent = len(line) - len(line.lstrip(' '))
        if cur_indent < fence_indent_len:
            check_k = k
            while check_k >= 0:
                chk_line = lines[check_k]
                chk_stripped = chk_line.strip()
                if not chk_stripped:
                    check_k -= 1
                    continue
                chk_indent = len(chk_line) - len(chk_line.lstrip(' '))
                if chk_indent <= cur_indent:
                    if LIST_MARKER_RE.match(chk_stripped):
                        return True, cur_indent
                    if chk_indent == 0:
                        return False, 0
                check_k -= 1
            return False, 0
        k -= 1
    return False, 0


def scan_indented_fences(lines: List[str],
                         warn_func: Optional[Callable[[str], None]] = None) -> List[Dict[str, Any]]:
    """Ограды с отступом внутри списков: начало, конец, отступ, язык и строки кода без базового отступа."""
    blocks = []
    i, n = 0, len(lines)
    while i < n:
        m = OPEN_FENCE_RE.match(lines[i])
        if m:
            open_indent = m.group('indent')
            fence_str = m.group('fence')
            fence_char, fence_len = fence_str[0], len(fence_str)
            lang = m.group('lang') or ''
            indent_len = len(open_indent)
            in_list, target_indent = find_list_context(lines, i, indent_len)
            if indent_len >= 4 and not in_list:      # обычный блок кода CommonMark
                i += 1
                continue
            code_lines, j, closed = [], i + 1, False
            while j < n:
                cur_line = lines[j]
                stripped = cur_line.strip()
                if stripped.startswith(fence_char * fence_len):
                    cm = CLOSE_FENCE_RE.match(cur_line)
                    if cm and cm.group('fence')[0] == fence_char \
                            and len(cm.group('fence')) >= fence_len \
                            and len(cm.group('indent')) <= indent_len:
                        closed = True
                        break
                cur_indent_len = len(cur_line) - len(cur_line.lstrip(' '))
                if stripped and cur_indent_len < indent_len:   # обрыв: незакрытая ограда
                    if warn_func:
                        warn_func(f"Unclosed fence starting at line {i + 1}")
                    break
                code_lines.append(cur_line)
                j += 1
            if closed:
                clean = []
                for c in code_lines:
                    if c.startswith(open_indent):
                        clean.append(c[indent_len:])
                    elif not c.strip():
                        clean.append('')
                    else:
                        clean.append(c.lstrip(' '))
                blocks.append({'start_line': i, 'end_line': j, 'open_indent': open_indent,
                               'in_list': in_list, 'target_indent': target_indent,
                               'lang': lang, 'code_lines': clean})
                i = j + 1
                continue
            if warn_func and j == n:
                warn_func(f"Unclosed fence starting at line {i + 1}")
        i += 1
    return blocks


class UnifiedCodeLineMask:
    """Номера строк (с 0) текста единицы, которые Python-Markdown выведет кодом.

    include_indented обязан быть равен флагу препроцессора оград с отступом (indented_fences):
    пока препроцессор выключен, такие ограды выводятся текстом и кодом не считаются.
    """

    def __init__(self, target_text: str, md: markdown.Markdown, include_indented: bool):
        raw_lines = target_text.split('\n')
        self.num_lines = len(raw_lines)
        norm_lines = md.preprocessors['normalize_whitespace'].run(raw_lines)
        norm_str = '\n'.join(norm_lines)
        starts = [0]
        for line in norm_lines:
            starts.append(starts[-1] + len(line) + 1)
        self.lines: Set[int] = set()
        self.blocks: List[Tuple[int, int]] = []
        for m in FencedBlockPreprocessor.FENCED_BLOCK_RE.finditer(norm_str):
            first = bisect_right(starts, m.start()) - 1
            last = bisect_right(starts, m.end() - 1) - 1
            self._add(first, last)
        if include_indented:
            for b in scan_indented_fences(norm_lines):
                self._add(b['start_line'], b['end_line'])
        self.blocks.sort()

    def _add(self, first: int, last: int) -> None:
        last = min(last, self.num_lines - 1)
        if first > last:
            return
        self.blocks.append((first, last))
        self.lines.update(range(first, last + 1))

    def is_line_in_code(self, line_num: int) -> bool:
        return line_num in self.lines
