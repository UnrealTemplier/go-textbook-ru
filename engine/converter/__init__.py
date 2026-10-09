"""
engine/converter/__init__.py
Преобразование Markdown-статей в чистый семантический HTML5.
Обработка Callouts, Mermaid диаграмм, Prism.js подсветки, Wikilinks и TOC.
"""

import re
import html
import textwrap
from typing import Tuple, Dict, Any, List, Optional
import markdown
from ..config import BookConfig
from ..scanner import slugify, Article, KnowledgeBaseScanner, find_first_h1, duplicate_h1
from .indented_fence import IndentedFenceExtension
from .math_protect import MathProtectExtension
from .obsidian_lists import ObsidianListsExtension
from .code_mask import UnifiedCodeLineMask, INLINE_CODE_RE
from .callouts import CalloutExtractor
from .headings import HeadingIdsExtension, escape_trailing_hashes
from ..hooks import load_hooks

CALLOUT_CONFIG = {
    "tip": {
        "icon": "💡",
        "class": "callout-tip",
        "color": "var(--accent-emerald)"
    },
    "interview": {
        "icon": "🎯",
        "class": "callout-interview",
        "color": "var(--accent-cyan)"
    },
    "info": {
        "icon": "⚙️",
        "class": "callout-info",
        "color": "var(--accent-indigo)"
    },
    "warning": {
        "icon": "⚠️",
        "class": "callout-warning",
        "color": "var(--accent-amber)"
    },
    "note": {
        "icon": "📝",
        "class": "callout-note",
        "color": "var(--accent-cyan)"
    },
    "important": {
        "icon": "⚡",
        "class": "callout-important",
        "color": "var(--accent-indigo)"
    },
    "caution": {
        "icon": "🛑",
        "class": "callout-caution",
        "color": "var(--accent-rose)"
    },
    "danger": {
        "icon": "🚨",
        "class": "callout-danger",
        "color": "var(--accent-rose)"
    }
}

def unique_slug(slug: str, used: set) -> str:
    """Первое вхождение сохраняет slug, повторы получают -2, -3, … (без совпадения с занятыми)."""
    if slug not in used:
        used.add(slug)
        return slug
    n = 2
    while f"{slug}-{n}" in used:
        n += 1
    used.add(f"{slug}-{n}")
    return f"{slug}-{n}"


class MarkdownConverter:
    def __init__(self, scanner: Optional[KnowledgeBaseScanner], config: Optional[BookConfig] = None):
        self.scanner = scanner
        self.config = config or (scanner.config if scanner is not None else BookConfig())
        self.warnings: List[str] = []
        self.current_article: Optional[Article] = None
        extensions = ["fenced_code", "tables", "sane_lists", "nl2br", HeadingIdsExtension()]
        mcfg = self.config.markdown
        if mcfg.indented_fences:
            extensions.append(IndentedFenceExtension(self.warnings.append))
        if mcfg.obsidian_lists:
            extensions.append(ObsidianListsExtension())
        if self.config.math.protect:
            extensions.append(MathProtectExtension(self.config.math.delimiters, self.config.math.protect))
        self.md = markdown.Markdown(extensions=extensions)

    def convert_article(self, article: Article) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Полный цикл конвертации статьи из файла .md в HTML.
        Возвращает (html_body, table_of_contents).
        """
        self.current_article = article
        with open(article.source_path, "r", encoding="utf-8", errors="ignore") as fp:
            raw_text = fp.read()

        # 0. Хук книги transform_markdown, затем убираем из тела первый «# …», который дублирует
        #    заголовок страницы: при title_source = "h1" — всегда, иначе — точную копию (U14)
        raw_text = load_hooks(self.config).transform_markdown(raw_text, article)
        if self.config.content.title_source == "h1":
            h1 = find_first_h1(raw_text)
            h1_line = h1[0] if h1 is not None else None
        else:
            h1_line = duplicate_h1(raw_text, article.title)
        if h1_line is not None:
            lines = raw_text.split("\n")
            del lines[h1_line]
            raw_text = "\n".join(lines)

        # 1. Очистка от шаблонных фраз (вне кода: маска текста статьи)
        cleaned_text = self._clean_cliches(raw_text, self._mask(raw_text))

        # 2. Выделение и экранирование блоков Mermaid (чтобы markdown парсер не исказил их)
        mermaid_placeholders: Dict[str, str] = {}
        processed_text = self._extract_mermaid(cleaned_text, mermaid_placeholders)

        # 3. Выноски Obsidian → плейсхолдеры; тело каждой рендерится отдельно (маска, wikilinks, md)
        callout_placeholders: Dict[str, str] = {}
        processed_text = CalloutExtractor(self).extract_callouts(processed_text, callout_placeholders, article)

        # 4. Преобразование Wikilinks [[...]] вне кода (content.wikilinks = false — шаг выключен).
        #    Маска строится по тексту этого шага: Mermaid и выноски к этому моменту уже заменены.
        if self.config.content.wikilinks:
            processed_text = self._transform_wikilinks(processed_text, article, mask=self._mask(processed_text))

        # 5. Парсинг заголовков и простановка id-анкоров
        processed_text, toc = self._process_headings(processed_text)

        # 6. Основная конвертация через Python-Markdown; id заголовков H2–H4 — по TOC (только здесь,
        #    в вызовах для тел выносок список пуст и treeprocessor пассивен)
        self.md.reset()
        self.md.heading_slugs = [item["anchor"] for item in toc]
        try:
            html_content = self.md.convert(processed_text)
        finally:
            self.md.heading_slugs = None
            self.md.reset()

        # 7. Возврат Mermaid и выносок на свои места (до таблиц и блоков кода)
        for ph, m_code in mermaid_placeholders.items():
            html_content = html_content.replace(ph, m_code)
        for ph, box in callout_placeholders.items():
            html_content = html_content.replace(ph, box)

        # 8. Оборачивание таблиц в адаптивный контейнер
        html_content = self._wrap_tables(html_content)

        # 9. Оборачивание блоков кода с кнопкой «Скопировать»
        html_content = self._enhance_code_blocks(html_content)

        return html_content, toc

    def warn(self, message: str) -> None:
        where = self.current_article.source_path if self.current_article is not None else "?"
        self.warnings.append(f"{where}: {message}")

    def _mask(self, text: str) -> UnifiedCodeLineMask:
        """Маска кода единицы текста; ограды с отступом — только если их выводит препроцессор."""
        return UnifiedCodeLineMask(text, self.md, include_indented=self.config.markdown.indented_fences)

    def _clean_cliches(self, text: str, mask: Optional[UnifiedCodeLineMask] = None) -> str:
        """Удаление шаблонных фраз (content.clean_cliches в book.toml) из HTML; sources/ не меняется.

        mask — маска этого же текста: совпадение, которое начинается в строке кода, не трогается.
        """
        for pat in self.config.content.clean_cliches:
            if mask is None:
                text = re.sub(pat, "", text, flags=re.IGNORECASE)
                continue
            current = text

            def repl(m, current=current):
                line = current.count("\n", 0, m.start())
                return m.group(0) if mask.is_line_in_code(line) else ""
            text = re.sub(pat, repl, current, flags=re.IGNORECASE)
        return text

    def _extract_mermaid(self, text: str, placeholders: Dict[str, str]) -> str:
        """Извлечение диаграмм Mermaid и валидация их синтаксиса."""
        pattern = re.compile(r"```mermaid(.*?)```", re.DOTALL | re.IGNORECASE)

        idx = 0
        def repl(match):
            nonlocal idx
            # Отступы значимы для mindmap (и ряда других типов), поэтому строки не обрезаются
            # слева: убираем только пустые строки по краям, цитатные символы '> ' и общий отступ.
            raw_code = match.group(1).strip("\n")
            lines = []
            for l in raw_code.splitlines():
                l = l.rstrip()
                if l.lstrip().startswith(">"):
                    l = re.sub(r"^\s*>+ ?", "", l)
                lines.append(l)

            clean_code = textwrap.dedent("\n".join(lines)).strip()

            # Валидация и исправление узлов с незакавыченными скобками: A[Text (Info)] -> A["Text (Info)"]
            clean_code = self._sanitize_mermaid(clean_code)

            placeholder = f"<!--MERMAID_PLACEHOLDER_{idx}-->"
            idx += 1

            wrapped_html = f"""
<figure class="mermaid-wrapper" role="figure" aria-label="{self.config.t("mermaid.title")}">
  <figcaption class="mermaid-header">
    <div class="mermaid-title">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
      <span>{self.config.t("mermaid.title")}</span>
    </div>
    <button type="button" class="btn-mermaid-fullscreen" data-action="mermaid-fullscreen" title="{self.config.t("mermaid.fullscreen_title")}" aria-label="{self.config.t("mermaid.fullscreen_aria")}">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
      <span>{self.config.t("mermaid.fullscreen_text")}</span>
    </button>
  </figcaption>
  <pre class="mermaid">
{html.escape(clean_code)}
  </pre>
</figure>
"""
            placeholders[placeholder] = wrapped_html
            return f"\n\n{placeholder}\n\n"

        return pattern.sub(repl, text)

    # Заголовки диаграмм, к которым применяются автоисправления синтаксиса рёбер и узлов.
    _MERMAID_FLOW_HEADER = re.compile(r"\s*(?:flowchart|graph)\b")
    # Операторы связи flowchart: -->, ---, ==>, -.->, <-->, ~~~ и т.п.
    _MERMAID_LINK = r"(?:<?-{2,}>?|<?={2,}>?|-\.+-?>?|~~~)"

    @staticmethod
    def _outside_quotes(line: str, pos: int) -> bool:
        """True, если позиция pos в строке не находится внутри строки в двойных кавычках."""
        return line[:pos].count('"') % 2 == 0

    def _fix_flowchart_line(self, line: str) -> str:
        """Автоисправление типичных синтаксических ошибок flowchart/graph (Mermaid 10.9.1)."""
        # Толстая двунаправленная стрелка с квотированной меткой (недопустима):
        # A <==|"текст"|==> B  ->  A <== "текст" ==> B
        line = re.sub(r'<==\|"([^"]*)"\|==>', r'<== "\1" ==>', line)

        # Вложенные двойные кавычки в метке узла:
        # N["os.Open("/etc")"]  ->  N["os.Open(#quot;/etc#quot;)"]
        # Метка заканчивается на первом сочетании "] (соседние узлы строки не захватываются).
        def _escape_nested(m):
            return f'{m.group(1)}["{m.group(2).replace(chr(34), "#quot;")}"]'
        line = re.sub(r'(\w+)\["((?:(?!"\]).)+)"\]', _escape_nested, line)

        # Неквотированная метка ребра (скобки, двоеточия и т.п. ломают разбор):
        # A -->|open()| B  ->  A -->|"open()"| B
        line = re.sub(
            rf'({self._MERMAID_LINK})\|([^|"\n]+)\|',
            lambda m: f'{m.group(1)}|"{m.group(2).strip()}"|',
            line,
        )
        return line

    def _sanitize_mermaid(self, code: str) -> str:
        """Исправление типичных опечаток в Mermaid."""
        # 1. Если первая строка '>', убираем
        lines = code.splitlines()
        if lines and lines[0].strip() == ">":
            lines = lines[1:]

        is_flowchart = bool(lines) and bool(self._MERMAID_FLOW_HEADER.match(lines[0]))

        sanitized_lines = []
        for line in lines:
            # Оборачиваем скобки внутри узлов: id[Text (with parens)] -> id["Text (with parens)"]
            # Ищем квадратные скобки без кавычек внутри, содержащие круглые скобки.
            # Совпадение внутри уже квотированной метки (например, индексы срезов
            # Go: "dq[:len(dq)-1]") не трогаем — иначе схема ломается.
            m = re.search(r"(\w+)\s*\[([^\"\]]*\([^\"\]]*\)[^\"\]]*)\]", line)
            if m and self._outside_quotes(line, m.start()):
                node_id = m.group(1)
                label = m.group(2)
                line = line.replace(f"{node_id}[{label}]", f'{node_id}["{label}"]')

            # Оборачиваем форму БД: DB[(Database Text)] -> DB[("Database Text")]
            m_db = re.search(r"(\w+)\s*\[\(([^\"\]\)]+)\)\]", line)
            if m_db and self._outside_quotes(line, m_db.start()):
                node_id = m_db.group(1)
                label = m_db.group(2)
                line = line.replace(f"{node_id}[({label})]", f'{node_id}[("{label}")]')

            # Исправление опечатки назначения классов через запятую вместо пробела:
            # class Domain,succ; -> class Domain succ;
            m_class = re.match(r"^(\s*class\s+[a-zA-Z0-9_-]+(?:,\s*[a-zA-Z0-9_-]+)*),\s*([a-zA-Z0-9_-]+)\s*(;?)\s*$", line)
            if m_class:
                line = f"{m_class.group(1)} {m_class.group(2)}{m_class.group(3)}"

            # Синтаксис рёбер и кавычек во flowchart/graph
            if is_flowchart:
                line = self._fix_flowchart_line(line)

            sanitized_lines.append(line)

        return "\n".join(sanitized_lines)

    def _transform_callouts(self, text: str) -> str:
        """
        Преобразование Obsidian Callouts вида:
        > [!tip] Заголовок
        > Содержимое...
        в HTML контейнеры.
        """
        lines = text.splitlines()
        result_lines = []
        in_callout = False
        callout_type = "note"
        callout_title = ""
        callout_body: List[str] = []

        i = 0
        while i < len(lines):
            line = lines[i]
            # Начало callout
            m_start = re.match(r"^>\s*\[!([a-zA-Z0-9_-]+)\]\s*(.*)$", line)
            if m_start:
                if in_callout:
                    # Закрываем предыдущий callout
                    result_lines.append(self._render_callout_block(callout_type, callout_title, callout_body))
                    callout_body = []

                in_callout = True
                callout_type = m_start.group(1).lower()
                callout_title = m_start.group(2).strip()
                i += 1
                continue

            if in_callout:
                if line.startswith(">"):
                    # Продолжение цитаты callout
                    content = line[1:]
                    if content.startswith(" "):
                        content = content[1:]
                    callout_body.append(content)
                    i += 1
                    continue
                elif line.strip() == "":
                    # Пустая строка может быть внутри или концом callout
                    # Смотрим на следующую строку
                    if i + 1 < len(lines) and lines[i + 1].startswith(">"):
                        callout_body.append("")
                        i += 1
                        continue
                    else:
                        # Завершение callout
                        result_lines.append(self._render_callout_block(callout_type, callout_title, callout_body))
                        result_lines.append("")
                        in_callout = False
                        callout_body = []
                        i += 1
                        continue
                else:
                    # Выход из callout
                    result_lines.append(self._render_callout_block(callout_type, callout_title, callout_body))
                    in_callout = False
                    callout_body = []
                    result_lines.append(line)
                    i += 1
                    continue

            result_lines.append(line)
            i += 1

        if in_callout:
            result_lines.append(self._render_callout_block(callout_type, callout_title, callout_body))

        return "\n".join(result_lines)

    def _render_callout_block(self, callout_type: str, custom_title: str, body_lines: List[str]) -> str:
        """Генерация HTML для отдельного блока Callout."""
        cfg, title = self.callout_style(callout_type, custom_title)

        # Парсим внутренний markdown
        inner_md = "\n".join(body_lines)
        inner_html = self.md.convert(inner_md)
        self.md.reset()
        return load_hooks(self.config).render_callout(callout_type, title, self._callout_html(cfg, title, inner_html))

    @staticmethod
    def _callout_html(cfg: Dict[str, str], title: str, inner_html: str) -> str:
        """HTML выноски; его же собирает CalloutExtractor (плейсхолдеры, А3а′)."""
        return f"""
<aside class="callout {cfg['class']}" aria-label="{html.escape(title)}">
  <header class="callout-header">
    <span class="callout-icon" aria-hidden="true">{cfg['icon']}</span>
    <span class="callout-title">{html.escape(title)}</span>
  </header>
  <div class="callout-body">
    {inner_html}
  </div>
</aside>
"""

    def callout_style(self, callout_type: str, custom_title: str):
        """Оформление и заголовок выноски: тип (неизвестный → note), заголовок по умолчанию, эвристика."""
        callout_type = self.config.callouts.alias.get(callout_type, callout_type)
        if callout_type not in CALLOUT_CONFIG:
            self.warn(f"неизвестный тип выноски [!{callout_type}] — оформлено как note "
                      f"(задайте [callouts.alias] в book.toml)")
        known = callout_type if callout_type in CALLOUT_CONFIG else "note"
        cfg = CALLOUT_CONFIG[known]
        title = custom_title if custom_title else self.config.t(f"callouts.{known}")
        if self.config.callouts.interview_heuristic and (
                "собеседован" in title.lower() or "интервью" in title.lower() or "interview" in title.lower()):
            cfg = CALLOUT_CONFIG["interview"]
            if not custom_title:
                title = self.config.t("callouts.interview")
        return cfg, title

    def _transform_wikilinks(self, text: str, current_article: Article, mask=None) -> str:
        """Преобразование [[Target|Display]] в <a href="..." class="wikilink">.

        mask (UnifiedCodeLineMask по этому же тексту): строки кода не трогаются.
        Inline-код (U20): если код целиком — найденная ссылка `[[X]]`, он становится ссылкой
        с моноширинным текстом <a class="wikilink"><code>X</code></a>; иначе остаётся кодом
        буквально (данные вроде map[[2]int]T, массивы LeetCode, ненайденные названия).
        """
        pattern = re.compile(r"\[\[(.*?)\]\]")

        def resolve(raw_link):
            href, display_text = self.scanner.resolve_wikilink(raw_link, current_article.rel_output_path)
            ambiguous = self.scanner.ambiguous_link(raw_link)
            if ambiguous:
                self.warn(f"неоднозначная ссылка [[{raw_link}]]: подходят {', '.join(ambiguous)}")
            return href, display_text

        def repl(match):
            href, display_text = resolve(match.group(1).strip())
            if href:
                return f'<a href="{href}" class="wikilink">{html.escape(display_text)}</a>'
            else:
                return f'<span class="wikilink-unresolved" title="{self.config.t("content.wikilink_unresolved_title")}">{html.escape(display_text)}</span>'

        def code_span(match):
            whole = re.fullmatch(r"\s*\[\[(.+?)\]\]\s*", match.group(2))
            if whole:
                href, display_text = resolve(whole.group(1).strip())
                if href:
                    return f'<a href="{href}" class="wikilink"><code>{html.escape(display_text)}</code></a>'
            return match.group(0)

        def transform_line(line):
            # Что начинается раньше, то и разбирается: ссылка [[…]] (в том числе с `кодом` внутри)
            # или inline-код (правило U20 для `[[…]]`).
            if "[[" not in line:
                return line
            out, pos = [], 0
            while pos < len(line):
                link = pattern.search(line, pos)
                code = INLINE_CODE_RE.search(line, pos)
                if link is None and code is None:
                    break
                if code is None or (link is not None and link.start() < code.start()):
                    out.append(line[pos:link.start()])
                    out.append(repl(link))
                    pos = link.end()
                else:
                    out.append(line[pos:code.start()])
                    out.append(code_span(code))
                    pos = code.end()
            out.append(line[pos:])
            return "".join(out)

        lines = text.split("\n")
        return "\n".join(line if (mask is not None and mask.is_line_in_code(i)) else transform_line(line)
                         for i, line in enumerate(lines))

    def _process_headings(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Добавление id в заголовки H2..H4 и формирование оглавления (TOC).

        Строки внутри fenced code-блоков (``` или ~~~) игнорируются —
        иначе комментарии Makefile вида '## build: ...' ошибочно попадают в TOC.
        """
        lines = text.splitlines()
        toc = []
        out_lines = []
        in_code_block = False
        fence_marker = ""
        used_slugs = set()      # дедупликация id: повтор получает -2, -3, … (А3д)

        for line in lines:
            stripped = line.strip()
            # Определяем начало / конец fenced code-блока
            fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
            if fence_match:
                marker = fence_match.group(1)[0] * len(fence_match.group(1))
                if not in_code_block:
                    in_code_block = True
                    fence_marker = marker
                elif stripped.startswith(fence_marker):
                    in_code_block = False
                    fence_marker = ""
                out_lines.append(line)
                continue

            if in_code_block:
                out_lines.append(line)
                continue

            m = re.match(r"^(#{2,4})\s+(.+)$", line)
            if m:
                level = len(m.group(1))
                raw_title = m.group(2).strip()
                clean_title = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", raw_title)
                clean_title = re.sub(r"[`*_]", "", clean_title)
                h_slug = unique_slug(slugify(clean_title, self.config.slug.anchor), used_slugs)

                toc.append({
                    "level": level,
                    "title": clean_title,
                    "anchor": h_slug
                })

                # Заголовок остаётся Markdown (разметка внутри обрабатывается, U24); id по TOC
                # ставит HeadingTreeprocessor. Приклеенный хвост «#» экранируется (Е1).
                out_lines.append(escape_trailing_hashes(f'{m.group(1)} {raw_title}'))
            else:
                # Остальные заголовки (H1, H5, H6) разбирает Python-Markdown: '#' в конце он
                # считает закрывающей последовательностью даже без пробела ('C#' -> 'C').
                # Хвост, приклеенный к слову, экранируем; '# Текст #' не трогаем.
                out_lines.append(re.sub(
                    r"^(#{1,6}\s+.*[^\s#\\])(#+)\s*$",
                    lambda hm: hm.group(1) + "\\#" * len(hm.group(2)),
                    line,
                ))

        return "\n".join(out_lines), toc

    def _wrap_tables(self, html_text: str) -> str:
        """Оборачивание <table> в адаптивный контейнер с горизонтальным скроллом."""
        aria = self.config.t("content.table_aria")
        return re.sub(r"(<table>.*?</table>)", lambda m: f'<div class="table-container" role="region" aria-label="{aria}" tabindex="0">{m.group(1)}</div>', html_text, flags=re.DOTALL)

    def _enhance_code_blocks(self, html_text: str) -> str:
        """
        Улучшение блоков кода: добавление шапки с языком и кнопкой копирования.
        Поддерживает как блоки с явным языком, так и блоки без языка (text/diagram).
        """
        pattern = re.compile(r'<pre><code(?:\s+class="language-([a-zA-Z0-9_-]+)")?>(.*?)</code></pre>', re.DOTALL)

        def repl(match):
            lang_match = match.group(1)
            code_body = match.group(2)
            
            if lang_match:
                lang = lang_match.lower()
                display_lang = {
                    "go": "Go",
                    "c": "C",
                    "cpp": "C++",
                    "bash": "Bash",
                    "sh": "Shell",
                    "python": "Python",
                    "sql": "SQL",
                    "yaml": "YAML",
                    "json": "JSON",
                    "nasm": "Assembly (x86)",
                    "asm": "Assembly",
                    "text": "Text",
                    "txt": "Text",
                    "ascii": "ASCII Diagram"
                }.get(lang, lang.upper())
            else:
                # Если язык не указан, проверяем наличие символов псевдографики
                ascii_chars = set("┌┐└┘├┤┬┴┼─│═║╔╗╚╝╠╣╦╩╬►◄▲▼")
                if any(c in code_body for c in ascii_chars):
                    lang = "ascii"
                    display_lang = "DIAGRAM"
                else:
                    lang = "text"
                    display_lang = "TEXT"

            return f"""
<div class="code-block" data-lang="{lang}">
  <header class="code-header">
    <span class="code-lang-tag">{display_lang}</span>
    <button type="button" class="btn-code-copy" data-action="copy-code" title="{self.config.t("code.copy_title")}" aria-label="{self.config.t("code.copy_aria")}">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><use href="#icon-copy"></use></svg>
      <span>{self.config.t("code.copy_text")}</span>
    </button>
  </header>
  <pre class="language-{lang}"><code class="language-{lang}">{code_body}</code></pre>
</div>
"""

        return pattern.sub(repl, html_text)
