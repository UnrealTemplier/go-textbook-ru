"""
engine/scanner.py
Сканирование исходников ./sources, построение иерархической модели,
формирование путей и резолвер внутренних ссылок (wikilinks).
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Any

from .config import BookConfig, canonicalize_title


class ScanError(ValueError):
    """Ошибка структуры sources/: файл не попал бы на сайт или пути совпали."""


H1_RE = re.compile(r"^#[ \t]+(.+?)[ \t]*$")


def find_first_h1(content: str) -> Optional[Tuple[int, str]]:
    """Первый заголовок «# …» вне оград: (номер строки, текст) или None."""
    fence = ""
    for i, line in enumerate(content.split("\n")):
        stripped = line.strip()
        m = re.match(r"^(`{3,}|~{3,})", stripped)
        if m:
            marker = m.group(1)
            if not fence:
                fence = marker[0] * len(marker)
            elif stripped.startswith(fence):
                fence = ""
            continue
        if fence:
            continue
        h = H1_RE.match(line)
        if h:
            return i, h.group(1)
    return None

CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
    'я': 'ya'
}

def natural_sort_key(s: str) -> List[Any]:
    """Сортировка строк с учетом чисел (1, 2, 10 вместо 1, 10, 2)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]

def slugify(text: str, max_length: int = 60) -> str:
    """Генерация чистого URL-friendly slug из кириллицы/латиницы."""
    text = text.lower().strip()
    result = []
    for ch in text:
        if ch in CYRILLIC_TO_LATIN:
            result.append(CYRILLIC_TO_LATIN[ch])
        elif ch.isalnum():
            result.append(ch)
        elif ch in [' ', '-', '_', '.']:
            result.append('-')
    slug = "".join(result)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        slug = "item"
    return slug[:max_length].rstrip("-")

def normalize_key(text: str) -> str:
    """Нормализация строки для нечеткого сопоставления ссылок."""
    text = text.lower().strip()
    if text.endswith(".md"):
        text = text[:-3]
    text = re.sub(r"[^\w\sа-яёa-z0-9]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def extract_headings(content: str, anchor_length: int = 80) -> List[Tuple[int, str, str]]:
    """Извлечение всех заголовков H2, H3, H4 и их slug-анкоров.

    Игнорирует строки, находящиеся внутри fenced code-блоков (``` или ~~~),
    чтобы комментарии вида '## build: ...' внутри Makefile-блоков
    не попадали в Table of Contents.
    """
    headings = []
    in_code_block = False
    fence_marker = ""
    for line in content.splitlines():
        stripped = line.strip()
        # Определяем начало / конец fenced code-блока
        fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if not in_code_block:
                in_code_block = True
                fence_marker = marker[0] * len(marker)  # нормализуем до однородного маркера
            elif stripped.startswith(fence_marker):
                in_code_block = False
                fence_marker = ""
            continue
        if in_code_block:
            continue
        m = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if m:
            level = len(m.group(1))
            raw_title = m.group(2).strip()
            clean_title = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", raw_title)
            clean_title = re.sub(r"[`*_]", "", clean_title)
            anchor = slugify(clean_title, max_length=anchor_length)
            headings.append((level, raw_title, anchor))
    return headings

class Article:
    def __init__(
        self,
        title: str,
        source_path: str,
        rel_output_path: str,
        module_num: int,
        module_name: str,
        raw_filename: str = "",
        subsection_name: str = "",
        global_order: int = 0
    ):
        self.title = title
        self.raw_filename = raw_filename or title
        self.source_path = source_path
        self.rel_output_path = rel_output_path
        self.module_num = module_num
        self.module_name = module_name
        self.subsection_name = subsection_name
        self.global_order = global_order
        
        self.headings: List[Tuple[int, str, str]] = []
        self.prev_article: Optional['Article'] = None
        self.next_article: Optional['Article'] = None
        self.size_bytes: int = 0
        self.mermaid_count: int = 0
        self.is_index: bool = False      # заглавная страница своего каталога (content.index_file)
        self.position: int = 0           # номер среди страниц, кроме заглавных
        self.index_of: Optional[Dict[str, Any]] = None   # узел каталога, если это его заглавная страница
        self.module_index: Optional['Article'] = None    # заглавная страница модуля
        self.section_index: Optional['Article'] = None   # заглавная страница подраздела

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "rel_output_path": self.rel_output_path,
            "module_num": self.module_num,
            "module_name": self.module_name,
            "subsection_name": self.subsection_name,
            "global_order": self.global_order,
            "size_bytes": self.size_bytes,
            "mermaid_count": self.mermaid_count,
            "headings": [{"level": h[0], "title": h[1], "anchor": h[2]} for h in self.headings]
        }

class KnowledgeBaseScanner:
    def __init__(self, sources_dir: str, config: Optional[BookConfig] = None):
        self.sources_dir = os.path.abspath(sources_dir)
        self.config = config or BookConfig()
        self.slug = self.config.slug
        self._canon = lambda t: canonicalize_title(t, self.config.content.canonical_replacements)
        self.articles: List[Article] = []
        self.articles_by_path: Dict[str, Article] = {}
        self.wikilink_index: Dict[str, Article] = {}
        self.modules_tree: List[Dict[str, Any]] = []

    def scan(self) -> List[Article]:
        """Обход дерева sources/ произвольной глубины и построение графа связей.

        Модуль — каталог верхнего уровня с номером («N. Название»). Внутри модуля каталоги любой
        глубины; для шаблонов дерево отдаётся в виде «модуль → подразделы», где путь глубоких
        каталогов склеивается через « / ». Порядок страниц: файлы каталога, затем подкаталоги.
        Ситуации, в которых раньше файлы терялись молча, — ошибки сборки (ScanError).
        """
        entries = sorted(os.listdir(self.sources_dir), key=natural_sort_key)
        stray = [e for e in entries if os.path.isfile(os.path.join(self.sources_dir, e)) and e.endswith(".md")]
        if stray:
            raise ScanError(f"{self.sources_dir}: .md в корне не входят ни в один модуль: {stray}")
        top_dirs = [d for d in entries if os.path.isdir(os.path.join(self.sources_dir, d))]

        self._order = 0
        modules_tree = []
        seen_nums: Dict[int, str] = {}

        for top_dir in top_dirs:
            m_match = re.match(r"^(\d+)\.\s*(.*)$", top_dir)
            if not m_match:
                raise ScanError(f"каталог модуля без номера «N. Название»: {top_dir}")
            module_num = int(m_match.group(1))
            if module_num in seen_nums:
                raise ScanError(f"два модуля с номером {module_num}: {seen_nums[module_num]}, {top_dir}")
            seen_nums[module_num] = top_dir
            module_clean_title = m_match.group(2).strip()

            mod_slug = f"{module_num:02d}-{slugify(module_clean_title, self.slug.module)}"
            module_canonical_title = self._canon(module_clean_title)
            module_node = {
                "num": module_num,
                "raw_name": top_dir,
                "title": module_canonical_title,
                "slug": mod_slug,
                "subsections": [],
                "articles": [],
                "index": None,
            }
            self._walk(os.path.join(self.sources_dir, top_dir), module_node, [], [])
            modules_tree.append(module_node)
            for art in module_node["articles"] + ([module_node["index"]] if module_node["index"] else []):
                art.module_index = module_node["index"]
            for sub in module_node["subsections"]:
                for art in sub["articles"] + ([sub["index"]] if sub["index"] else []):
                    art.module_index = module_node["index"]
                    art.section_index = sub["index"]

        for i in range(len(self.articles)):
            if i > 0:
                self.articles[i].prev_article = self.articles[i - 1]
            if i < len(self.articles) - 1:
                self.articles[i].next_article = self.articles[i + 1]

        content = [a for a in self.articles if not a.is_index]
        for pos, art in enumerate(content, 1):
            art.position = pos
        self.content_count = len(content)
        self.has_index_pages = len(content) != len(self.articles)

        self.modules_tree = modules_tree
        self._build_wikilink_index()
        return self.articles

    def _walk(self, dir_path: str, module_node: Dict[str, Any], names: List[str], slugs: List[str]) -> None:
        """Каталог модуля (names пуст) или вложенный каталог любой глубины."""
        entries = sorted(os.listdir(dir_path), key=natural_sort_key)
        subdirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e))]
        files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e)) and e.endswith(".md")]
        index_re = self.config.content.index_file

        if names and subdirs:
            pages = [f for f in files if not (index_re and re.match(index_re, f))]
            if pages:
                raise ScanError(f"{dir_path}: статьи рядом с подкаталогами были бы потеряны: {pages} "
                                f"(рядом с подкаталогами допустим только индексный файл)")

        if names:
            node = {"name": " / ".join(names), "slug": "/".join(slugs), "articles": [], "index": None}
            if files:
                module_node["subsections"].append(node)
        else:
            node = module_node
        sub_name = node["name"] if names else ""
        out_dir = "/".join(["docs", module_node["slug"]] + slugs)

        for f in files:
            self._order += 1
            raw_title = f[:-3]
            file_src = os.path.join(dir_path, f)
            is_index = bool(index_re) and bool(re.match(index_re, f))
            title = self._title_from_h1(file_src) if self.config.content.title_source == "h1" else self._canon(raw_title)
            rel_out = f"{out_dir}/{slugify(raw_title, self.slug.page)}.html"
            if rel_out in self.articles_by_path:
                raise ScanError(f"совпадение выходных путей после обрезки slug: {rel_out} "
                                f"({self.articles_by_path[rel_out].source_path} и {file_src})")
            art = Article(
                title=title,
                source_path=file_src,
                rel_output_path=rel_out,
                module_num=module_node["num"],
                module_name=module_node["title"],
                raw_filename=raw_title,
                subsection_name=sub_name,
                global_order=self._order,
            )
            art.is_index = is_index
            self._populate_article_stats(art)
            self.articles.append(art)
            self.articles_by_path[rel_out] = art
            if is_index:
                node["index"] = art
                art.index_of = node
            else:
                node["articles"].append(art)

        for sd in subdirs:
            sd_path = os.path.join(dir_path, sd)
            if not names:
                has_children = any(os.path.isdir(os.path.join(sd_path, e)) for e in os.listdir(sd_path))
                seg = slugify(sd, self.slug.subsection[0] if has_children else self.slug.section)
            else:
                seg = slugify(sd, self.slug.subsection[1])
            self._walk(sd_path, module_node, names + [sd], slugs + [seg])

    @staticmethod
    def _title_from_h1(path: str) -> str:
        with open(path, encoding="utf-8", errors="ignore") as fp:
            h1 = find_first_h1(fp.read())
        if h1 is None:
            raise ScanError(f"{path}: title_source = \"h1\", но в файле нет заголовка «# …»")
        return h1[1]

    def _populate_article_stats(self, art: Article) -> None:
        try:
            art.size_bytes = os.path.getsize(art.source_path)
            with open(art.source_path, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
            art.headings = extract_headings(content, self.slug.anchor)
            art.mermaid_count = len(re.findall(r"```mermaid", content, re.IGNORECASE))
        except Exception:
            pass

    def _build_wikilink_index(self) -> None:
        for art in self.articles:
            # 1. По каноническому заголовку
            self.wikilink_index[art.title] = art
            self.wikilink_index[art.title + ".md"] = art

            norm = normalize_key(art.title)
            self.wikilink_index[norm] = art

            m = re.match(r"^\d+\.\s*(.+)$", art.title)
            if m:
                clean = m.group(1).strip()
                self.wikilink_index[clean] = art
                self.wikilink_index[normalize_key(clean)] = art

            # 2. По физическому имени файла на диске (если отличается)
            if art.raw_filename and art.raw_filename != art.title:
                self.wikilink_index[art.raw_filename] = art
                self.wikilink_index[art.raw_filename + ".md"] = art
                norm_raw = normalize_key(art.raw_filename)
                self.wikilink_index[norm_raw] = art
                m_raw = re.match(r"^\d+\.\s*(.+)$", art.raw_filename)
                if m_raw:
                    clean_raw = m_raw.group(1).strip()
                    self.wikilink_index[clean_raw] = art
                    self.wikilink_index[normalize_key(clean_raw)] = art

    def resolve_wikilink(self, link_raw: str, current_output_rel: str) -> Tuple[Optional[str], str]:
        if "|" in link_raw:
            parts = link_raw.split("|", 1)
            target_part = parts[0].strip()
            display_text = parts[1].strip()
        else:
            target_part = link_raw.strip()
            display_text = target_part

        # Разбираем возможный anchor.
        # ВАЖНО: символ '#' может быть частью названия статьи (например, 'C#', 'F#').
        # Стратегия: если '#' присутствует — сначала пробуем найти статью по полному имени
        # (с '#'). Только если статья НЕ найдена — считаем '#' разделителем anchor.
        target_name = target_part
        anchor_slug = ""

        if "#" in target_part:
            t_parts = target_part.split("#", 1)
            candidate_name = t_parts[0].strip()
            anchor_name = t_parts[1].strip()

            # Попытка найти статью по полному имени (с '#') — значит '#' часть названия
            full_art = self.wikilink_index.get(target_part)
            if not full_art:
                full_art = self.wikilink_index.get(normalize_key(target_part))
            if not full_art and re.match(r"^\d+\.\s*", target_part):
                m_full = re.match(r"^\d+\.\s*(.+)$", target_part)
                if m_full:
                    full_art = self.wikilink_index.get(normalize_key(m_full.group(1)))

            if full_art:
                # '#' является частью названия, не anchor-разделителем
                target_name = target_part
                anchor_slug = ""
            else:
                # '#' — разделитель anchor
                target_name = candidate_name
                if anchor_name:
                    clean_anchor = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", anchor_name)
                    clean_anchor = re.sub(r"[`*_]", "", clean_anchor)
                    anchor_slug = "#" + slugify(clean_anchor, self.slug.anchor)
                else:
                    anchor_slug = ""

        if not target_name:
            clean_display = display_text.lstrip("#")
            return anchor_slug, clean_display

        art = self.wikilink_index.get(target_name)
        if not art:
            art = self.wikilink_index.get(normalize_key(target_name))

        if not art:
            m = re.match(r"^\d+\.\s*(.+)$", target_name)
            if m:
                art = self.wikilink_index.get(normalize_key(m.group(1)))

        if art:
            curr_dir = os.path.dirname(current_output_rel)
            rel_href = os.path.relpath(art.rel_output_path, curr_dir).replace("\\", "/")
            full_href = rel_href + anchor_slug
            if display_text == target_part:
                display_text = art.title
            return full_href, display_text

        return None, display_text
