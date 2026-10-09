"""
engine/template.py
HTML5 шаблоны, CSS стили в стиле Go Workout (Dark Theme) и JS скрипты для
автономной работы портала (file:/// и веб-хостинг).
"""

import os
import re
import html
import json
from string import Template
from typing import Dict, Any, List, Optional
from .config import BookConfig, read_text_asset
from .hooks import load_hooks

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
_PARTIALS: Dict[Any, Template] = {}


# Иконки, которые повторяются на странице: геометрия один раз в скрытом спрайте, в разметке —
# <use href="#…"> (ссылка внутри документа работает и по file://, в отличие от внешнего спрайта)
ICON_SPRITE = (
    '<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">'
    '<symbol id="icon-copy" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></symbol></svg>'
)

_CODE_LIKE_RE = re.compile(r"<(pre|code|script|style|textarea|option)\b.*?</\1>", re.S)


def page_needs(article_html: str, config: BookConfig) -> Dict[str, bool]:
    """Какие библиотеки нужны странице: Mermaid (pre.mermaid), Prism (блоки кода), KaTeX (формулы).

    KaTeX — консервативно: любой левый разделитель из [math].delimiters в тексте вне кода.
    Лишнее подключение безопасно, пропуск стоил бы формул (сверяется рантайм-проекцией).
    Без features.conditional_scripts нужно всё.
    """
    if not config.features.conditional_scripts:
        return {"mermaid": True, "prism": True, "katex": True}
    text = _CODE_LIKE_RE.sub("", article_html)
    return {
        "mermaid": '<pre class="mermaid">' in article_html,
        "prism": 'class="code-block"' in article_html,
        "katex": any(d["left"] in text for d in config.math.delimiters),
    }


def extra_asset_tags(config: BookConfig, rel_root: str, kind: str) -> str:
    """<link>/<script> для extra.css / extra.js книги, если они есть (иначе пустая строка)."""
    name = "extra.css" if kind == "css" else "extra.js"
    if not os.path.isfile(config.path(os.path.join(config.layout.extra_assets_dir, name))):
        return ""
    if kind == "css":
        return f'\n  <link rel="stylesheet" href="{asset_url(rel_root, "assets/extra.css")}">'
    return f'\n  <script src="{asset_url(rel_root, "assets/extra.js")}"></script>'


def partial(name: str, config: BookConfig, ctx: Dict[str, Any]) -> str:
    """Частичный шаблон: book/overrides/templates/<name>.html книги или engine/templates/<name>.html.

    Подстановки — string.Template ($имя): фигурные скобки CSS и JS в шаблонах не мешают.
    """
    key = (config.root_dir, config.layout.overrides_dir, name)
    if key not in _PARTIALS:
        override = config.path(os.path.join(config.layout.overrides_dir, "templates", name + ".html"))
        path = override if os.path.isfile(override) else os.path.join(TEMPLATES_DIR, name + ".html")
        with open(path, encoding="utf-8") as fp:
            _PARTIALS[key] = Template(fp.read().rstrip("\n"))
    return _PARTIALS[key].substitute(ctx)
from .scanner import Article

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


def get_project_version(version_file: str, pattern: str) -> str:
    """
    Версия из файла (для go-textbook — AGENTS.md § 1.4): ровно одно совпадение шаблона, SemVer.
    Шаблон — регулярное выражение с одной группой (MULTILINE), задаётся в book.toml.
    """
    if not os.path.isfile(version_file):
        raise FileNotFoundError(f"[VERSION ERROR] Canonical version file not found: {version_file}")

    with open(version_file, "r", encoding="utf-8") as fp:
        content = fp.read()

    matches = list(re.compile(pattern, re.MULTILINE).finditer(content))

    if len(matches) == 0:
        raise ValueError(
            f"[VERSION ERROR] Project version definition not found in {version_file}. "
            "Expected entry such as: '* **Current project version:** `1.1.0`'"
        )

    if len(matches) > 1:
        raise ValueError(
            f"[VERSION ERROR] Multiple canonical version declarations found in {version_file} ({len(matches)} occurrences). "
            "Exactly one canonical version declaration is allowed to prevent desynchronization."
        )

    version_raw = matches[0].group(1).strip()
    _check_semver(version_raw, version_file)
    return version_raw


def _check_semver(version: str, where: str) -> None:
    if not SEMVER_RE.match(version):
        raise ValueError(
            f"[VERSION ERROR] Invalid project version format '{version}' found in {where}. "
            "Version must strictly comply with semantic versioning (MAJOR.MINOR.PATCH, e.g. 1.1.0)."
        )


def get_book_version(config: BookConfig) -> str:
    """Версия книги: project.version или project.version_file + project.version_pattern."""
    p = config.project
    if p.version:
        _check_semver(p.version, "book.toml")
        return p.version
    if p.version_file:
        return get_project_version(config.path(p.version_file), p.version_pattern)
    raise ValueError("[VERSION ERROR] book.toml: не задана project.version или project.version_file")


def _load_themes_manifest():
    """Загружает manifest.json из engine/assets/themes/ для динамической генерации тем."""
    here = os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(here, "assets", "themes", "manifest.json")
    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("default", "dark"), data.get("themes", [])
    except Exception:
        # Fallback к хардкодным значениям
        return "dark", [
            {"key": "paper", "label": "Paper", "icon": "document"},
            {"key": "light", "label": "Light", "icon": "sun"},
            {"key": "dark",  "label": "Dark",  "icon": "moon"},
        ]

# Функции рантайма книги (анализ § 4.9): один источник для anti-flicker в <head> и для main.js.
_BOOK_RUNTIME_JS = (
    "window.__BOOK__=(function(c){"
    "function storageKey(n){return c.storagePrefix+n;}"
    "function getTheme(){try{var t=localStorage.getItem(storageKey('theme'));"
    "if(t&&c.availableThemes.indexOf(t)!==-1)return t;}catch(e){}return c.defaultTheme;}"
    "function applyTheme(t){var th=(t&&c.availableThemes.indexOf(t)!==-1)?t:c.defaultTheme;"
    "document.documentElement.dataset.theme=th;return th;}"
    "function saveTheme(t){try{localStorage.setItem(storageKey('theme'),t);}catch(e){}}"
    "function init(){try{applyTheme(getTheme());}catch(e){}}"
    "c.storageKey=storageKey;c.getTheme=getTheme;c.applyTheme=applyTheme;c.saveTheme=saveTheme;c.init=init;"
    "return c;})(%s);window.__BOOK__.init();"
)


def book_runtime_data(config: BookConfig) -> Dict[str, Any]:
    default_theme, themes = _load_themes_manifest()
    m = config.math
    return {
        "storagePrefix": config.project.storage_prefix,
        "defaultTheme": default_theme,
        "availableThemes": [t["key"] for t in themes],
        "themeNames": {t["key"]: t["label"] for t in themes},
        "strings": {"copied": config.t("js.copied"), "themeLabel": config.t("js.theme_label")},
        "math": {"delimiters": m.delimiters, "ignoredTags": m.ignored_tags, "ignoredClasses": m.ignored_classes},
    }


def make_anti_flicker_script(config: BookConfig) -> str:
    """Первый скрипт <head>: объявляет window.__BOOK__ (конфиг книги и функции темы) и ставит тему до отрисовки."""
    if not hasattr(config, "_runtime_script"):
        data = json.dumps(book_runtime_data(config), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        config._runtime_script = "<script>/* Book runtime + theme anti-flicker */" + (_BOOK_RUNTIME_JS % data) + "</script>"
    return config._runtime_script


# Версии ассетов для кэш-бастинга ?v=: первые 10 символов sha256 файла, уже записанного в dist/
ASSET_VERSIONS: Dict[str, str] = {}
VERSIONED_ASSETS = ["assets/style.css", "assets/main.js", "assets/search-data.js",
                    "assets/nav-data.js", "assets/extra.css", "assets/extra.js"]


def set_asset_versions(dist_dir: str, rel_paths: List[str]) -> None:
    """Вызывается сборкой после записи ассетов: хэш считается один раз за сборку."""
    import hashlib
    ASSET_VERSIONS.clear()
    for rel in rel_paths:
        path = os.path.join(dist_dir, rel)
        if os.path.isfile(path):
            with open(path, "rb") as fp:
                ASSET_VERSIONS[rel] = hashlib.sha256(fp.read()).hexdigest()[:10]


def asset_url(rel_root: str, rel_asset_path: str) -> str:
    """URL ассета от rel_root страницы, с ?v=<хэш>, если хэш известен."""
    v = ASSET_VERSIONS.get(rel_asset_path)
    return f"{rel_root}{rel_asset_path}" + (f"?v={v}" if v else "")

def theme_switcher_html(config: BookConfig) -> str:
    aria = config.t("page.theme_switcher_aria")
    return (
    '<button type="button" id="theme-switcher-btn" class="floating-theme-switcher" '
    'data-action="toggle-theme" '
    f'aria-label="{aria}">\n'
    '    <span class="theme-icon-slot" aria-hidden="true">\n'
    '      <svg class="theme-icon theme-icon-paper" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n'
    '        <path d="M16 2H8a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"></path>\n'
    '        <path d="M4 6v14a2 2 0 0 0 2 2h10"></path>\n'
    '        <line x1="10" y1="7" x2="14" y2="7"></line>\n'
    '        <line x1="10" y1="11" x2="14" y2="11"></line>\n'
    '      </svg>\n'
    '      <svg class="theme-icon theme-icon-light" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n'
    '        <circle cx="12" cy="12" r="5"></circle>\n'
    '        <line x1="12" y1="1" x2="12" y2="3"></line>\n'
    '        <line x1="12" y1="21" x2="12" y2="23"></line>\n'
    '        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>\n'
    '        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>\n'
    '        <line x1="1" y1="12" x2="3" y2="12"></line>\n'
    '        <line x1="21" y1="12" x2="23" y2="12"></line>\n'
    '        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>\n'
    '        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>\n'
    '      </svg>\n'
    '      <svg class="theme-icon theme-icon-dark" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n'
    '        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>\n'
    '      </svg>\n'
    '    </span>\n'
    '  </button>'
    )

def make_html_tag() -> str:
    """Генерирует открывающий тег <html> с атрибутами тем из manifest.json."""
    default_theme, themes = _load_themes_manifest()
    theme_keys = ','.join(t['key'] for t in themes)
    theme_labels = ','.join(f"{t['key']}:{t['label']}" for t in themes)
    return f'<html lang="ru" data-theme="{default_theme}" data-available-themes="{theme_keys}" data-theme-labels="{theme_labels}">'

def render_favicon_links(config: BookConfig, rel_root: str) -> str:
    b = config.branding
    links = []
    if b.favicon_ico:
        links.append(f'<link rel="icon" href="{rel_root}{os.path.basename(b.favicon_ico)}" sizes="32x32">')
    if b.favicon_svg:
        links.append(f'<link rel="icon" type="image/svg+xml" href="{rel_root}{os.path.basename(b.favicon_svg)}" sizes="any">')
    return "\n  ".join(links)


def fill_counts(text: str, counts: Dict[str, Any]) -> str:
    """Подстановки текстов главной: {modules}, {articles}, {articles_grouped}, {mermaid}."""
    for key, value in counts.items():
        text = text.replace("{" + key + "}", str(value))
    return text


def get_rel_root(rel_path: str) -> str:
    """Вычисление пути к корню сайта из относительного пути файла."""
    depth = rel_path.count("/")
    if depth == 0:
        return "./"
    return "../" * depth

def _first_page(mod: Dict[str, Any]) -> Optional[Article]:
    if mod.get("index"):
        return mod["index"]
    if mod["articles"]:
        return mod["articles"][0]
    for sub in mod["subsections"]:
        if sub.get("index") or sub["articles"]:
            return sub.get("index") or sub["articles"][0]
    return None


def render_sidebar(
    modules_tree: List[Dict[str, Any]],
    current_article: Optional[Article],
    rel_root: str,
    hybrid: bool = False,
    static_module_list: bool = True
) -> str:
    """Генерация интерактивного сайдбара с древовидным аккордеоном.

    hybrid: текущий модуль выводится полностью, остальные — заглушкой со ссылкой на первую
    страницу (static_module_list) или не выводятся вовсе; main.js достраивает их из nav-data.js.
    """
    html_parts = []
    html_parts.append('<div class="sidebar-nav">')

    curr_path = current_article.rel_output_path if current_article else ""

    for mod in modules_tree:
        mod_num = mod["num"]
        if hybrid and not (current_article and current_article.module_num == mod_num):
            if not static_module_list:
                continue
            first = _first_page(mod)
            mod_text = html.escape(mod["title"])
            if mod.get("index"):
                mod_text = _index_link(mod["index"], mod_text, rel_root, current_article)
            html_parts.append(f'<details class="nav-module" data-nav-module="{mod_num}">')
            html_parts.append(f'<summary class="nav-module-title"><span class="mod-badge">{mod_num}</span> <span class="mod-text">{mod_text}</span></summary>')
            html_parts.append(f'<div class="nav-module-content" data-nav-stub="1">')
            if first is not None:
                html_parts.append('<ul class="nav-articles-list">')
                html_parts.append(f'<li class="nav-item"><a href="{rel_root}{first.rel_output_path}">{html.escape(first.title)}</a></li>')
                html_parts.append('</ul>')
            html_parts.append('</div>')
            html_parts.append('</details>')
            continue
        mod_title = mod["title"]
        mod_raw = mod["raw_name"]
        
        # Проверяем, активен ли текущий модуль
        is_mod_active = False
        if current_article and current_article.module_num == mod_num:
            is_mod_active = True

        open_attr = "open" if is_mod_active else ""
        active_class = "active-module" if is_mod_active else ""

        nav_attr = f' data-nav-module="{mod_num}"' if hybrid else ''
        html_parts.append(f'<details class="nav-module {active_class}" {open_attr}{nav_attr}>')
        mod_text = html.escape(mod_title)
        if mod.get("index"):
            mod_text = _index_link(mod["index"], mod_text, rel_root, current_article)
        html_parts.append(f'<summary class="nav-module-title"><span class="mod-badge">{mod_num}</span> <span class="mod-text">{mod_text}</span></summary>')
        html_parts.append('<div class="nav-module-content">')

        # Статьи в корне модуля
        if mod["articles"]:
            html_parts.append('<ul class="nav-articles-list">')
            for art in mod["articles"]:
                href = rel_root + art.rel_output_path
                is_curr = (art.rel_output_path == curr_path)
                curr_class = ' class="nav-item active"' if is_curr else ' class="nav-item"'
                aria_cur = ' aria-current="page"' if is_curr else ''
                html_parts.append(f'<li{curr_class}><a href="{href}"{aria_cur}>{html.escape(art.title)}</a></li>')
            html_parts.append('</ul>')

        # Подразделы
        for sub in mod["subsections"]:
            sub_name = sub["name"]
            is_sub_active = False
            if current_article and current_article.subsection_name == sub_name and current_article.module_num == mod_num:
                is_sub_active = True

            sub_open = "open" if is_sub_active else ""
            active_sub_class = " active-submodule" if is_sub_active else ""
            html_parts.append(f'<details class="nav-submodule{active_sub_class}" {sub_open}>')
            html_parts.append(f'<summary class="nav-submodule-title"><span class="sub-chevron" aria-hidden="true"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"></polyline></svg></span><span class="sub-text">{_index_link(sub["index"], html.escape(sub_name), rel_root, current_article) if sub.get("index") else html.escape(sub_name)}</span></summary>')
            html_parts.append('<ul class="nav-articles-list sub-list">')
            for art in sub["articles"]:
                href = rel_root + art.rel_output_path
                is_curr = (art.rel_output_path == curr_path)
                curr_class = ' class="nav-item active"' if is_curr else ' class="nav-item"'
                aria_cur = ' aria-current="page"' if is_curr else ''
                html_parts.append(f'<li{curr_class}><a href="{href}"{aria_cur}>{html.escape(art.title)}</a></li>')
            html_parts.append('</ul>')
            html_parts.append('</details>')

        html_parts.append('</div>') # nav-module-content
        html_parts.append('</details>') # nav-module

    html_parts.append('</div>') # sidebar-nav
    return "\n".join(html_parts)

def _index_link(index: Article, text: str, rel_root: str, current: Optional[Article],
                css_class: str = "index-link") -> str:
    """Ссылка на заглавную страницу каталога (сайдбар — index-link, хлебные крошки — crumb-link)."""
    if current is index:
        return f'<a href="{rel_root}{index.rel_output_path}" class="{css_class} active" aria-current="page">{text}</a>'
    return f'<a href="{rel_root}{index.rel_output_path}" class="{css_class}">{text}</a>'


def render_index_children(article: Article, rel_root: str) -> str:
    """Список дочерних страниц под текстом заглавной страницы каталога (U22)."""
    node = article.index_of or {}
    items = []
    for art in node.get("articles", []):
        items.append(f'<li><a href="{rel_root}{art.rel_output_path}">{html.escape(art.title)}</a></li>')
    for sub in node.get("subsections", []):
        target = sub["index"] or (sub["articles"][0] if sub["articles"] else None)
        if target is not None:
            title = sub["index"].title if sub["index"] else sub["name"]
            items.append(f'<li><a href="{rel_root}{target.rel_output_path}">{html.escape(title)}</a></li>')
    if not items:
        return ""
    return '\n<ul class="index-children">\n' + "\n".join(items) + '\n</ul>\n'


def render_breadcrumbs(article: Article, rel_root: str, config: BookConfig) -> str:
    """Хлебные крошки над статьей."""
    crumbs = [
        f'<li class="crumb-item"><a href="{rel_root}index.html" class="crumb-link">{config.t("breadcrumbs.home")}</a></li>'
    ]
    crumbs.append('<li class="crumb-sep" aria-hidden="true">/</li>')
    mod_text = html.escape(article.module_name)
    if article.module_index is not None and article.module_index is not article:
        mod_text = _index_link(article.module_index, mod_text, rel_root, article, "crumb-link")
    crumbs.append(f'<li class="crumb-item crumb-module">{mod_text}</li>')
    
    if article.subsection_name:
        sub_text = html.escape(article.subsection_name)
        if article.section_index is not None and article.section_index is not article:
            sub_text = _index_link(article.section_index, sub_text, rel_root, article, "crumb-link")
        crumbs.append('<li class="crumb-sep" aria-hidden="true">/</li>')
        crumbs.append(f'<li class="crumb-item crumb-sub">{sub_text}</li>')

    crumbs.append('<li class="crumb-sep" aria-hidden="true">/</li>')
    crumbs.append(f'<li class="crumb-item crumb-current" aria-current="page">{html.escape(article.title)}</li>')

    return f'<nav class="breadcrumbs" aria-label="{config.t("breadcrumbs.aria")}"><ol class="breadcrumbs-list">{" ".join(crumbs)}</ol></nav>'

def render_article_page(
    article: Article,
    article_html: str,
    toc: List[Dict[str, Any]],
    modules_tree: List[Dict[str, Any]],
    total_articles: int,
    version: str,
    config: BookConfig,
    show_position: bool = False
) -> str:
    """Генерация полной HTML-страницы статьи. show_position — счётчик «N из M» (книги с индексными файлами)."""
    rel_root = get_rel_root(article.rel_output_path)
    hybrid = config.navigation.mode == "hybrid"
    sidebar_html = render_sidebar(modules_tree, article, rel_root, hybrid, config.navigation.static_module_list)
    breadcrumbs_html = render_breadcrumbs(article, rel_root, config)

    # Предыдущая и следующая статья
    prev_link_html = ""
    if article.prev_article:
        p_href = rel_root + article.prev_article.rel_output_path
        prev_link_html = f"""
<a href="{p_href}" class="article-nav-card prev-card" rel="prev">
  <span class="nav-dir">{config.t("article.prev")}</span>
  <span class="nav-title">{html.escape(article.prev_article.title)}</span>
</a>
"""
    else:
        prev_link_html = '<div class="article-nav-placeholder" aria-hidden="true"></div>'

    next_link_html = ""
    if article.next_article:
        n_href = rel_root + article.next_article.rel_output_path
        next_link_html = f"""
<a href="{n_href}" class="article-nav-card next-card" rel="next">
  <span class="nav-dir">{config.t("article.next")}</span>
  <span class="nav-title">{html.escape(article.next_article.title)}</span>
</a>
"""
    else:
        next_link_html = '<div class="article-nav-placeholder" aria-hidden="true"></div>'

    # Оглавление статьи (TOC)
    toc_items = []
    if toc:
        for t in toc:
            level = t["level"]
            cls = f"toc-item toc-h{level}"
            toc_items.append(f'<li class="{cls}"><a href="#{t["anchor"]}">{html.escape(t["title"])}</a></li>')
        toc_html = f"""
<aside class="article-toc" id="article-toc" aria-label="{config.t("article.toc_aria")}">
  <header class="toc-header">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
    <span>{config.t("article.toc_title")}</span>
  </header>
  <ul class="toc-list">
    {"".join(toc_items)}
  </ul>
</aside>
"""
    else:
        toc_html = ""

    rt = config.navigation.reading_time
    reading_time = max(rt.min, int(article.size_bytes / rt.divisor))
    ap = config.article_page
    br = config.branding
    footer_html = "\n        ".join(f"<p>{line}</p>" for line in ap.footer_html)
    position_html = ""
    if show_position and not article.is_index:
        position_html = f'\n              <span class="meta-tag position-tag">{config.t("article.position", n=article.position, m=total_articles)}</span>'
    if article.is_index:
        article_html += render_index_children(article, rel_root)
    needs = page_needs(article_html, config)
    icon_sprite = f"\n  {ICON_SPRITE}" if needs["prism"] else ""
    head_lines = []
    if needs["katex"]:
        head_lines.append(f'  <link rel="stylesheet" href="{rel_root}assets/vendor/katex/katex.min.css">')
    extra_css = extra_asset_tags(config, rel_root, "css")
    if extra_css:
        head_lines.append(extra_css.lstrip("\n"))
    if hybrid:
        head_lines.append(f'  <script src="{asset_url(rel_root, "assets/nav-data.js")}" defer></script>')
    head_extra = "\n".join(head_lines)
    vendor_scripts = "".join(
        f'  <script src="{rel_root}assets/vendor/{src}"></script>\n' for src, need in (
            ("prism-bundle.min.js", needs["prism"]), ("mermaid.min.js", needs["mermaid"]),
            ("katex/katex.min.js", needs["katex"]), ("katex/contrib/auto-render.min.js", needs["katex"]))
        if need)
    mermaid_tag = (f'<span class="meta-tag mermaid-tag">{config.t("article.mermaid_count", n=article.mermaid_count)}</span>'
                   if article.mermaid_count > 0 else '')
    ctx = {
        "rel_root": rel_root,
        "logo_aria_label": br.logo_aria_label,
        "logo_icon": read_text_asset(config, br.logo_icon_svg_file),
        "logo_title": read_text_asset(config, br.logo_title_svg_file),
        "logo_title_text": br.logo_title_text,
        "logo_sub": br.logo_sub,
        "module_tag": config.t("article.module_tag", n=article.module_num),
        "reading_time": config.t("article.reading_time", n=reading_time),
        "mermaid_tag": mermaid_tag,
        "position": position_html,
        "title": html.escape(article.title),
        "footer": footer_html,
    }
    load_hooks(config).page_context(article, ctx)

    return f"""<!DOCTYPE html>
{make_html_tag()}
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(article.title)}{ap.title_suffix_html}</title>
  <meta name="description" content="{ap.meta_description_html.replace('{title}', html.escape(article.title))}">
  {render_favicon_links(config, rel_root)}
  {make_anti_flicker_script(config)}
  <link rel="stylesheet" href="{asset_url(rel_root, 'assets/style.css')}">
{head_extra}
</head>
<body>{icon_sprite}
  <div class="reading-progress-bar" id="reading-progress" role="progressbar" aria-label="{config.t("page.reading_progress_aria")}" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>

  <div class="app-layout">
    <!-- Левый сайдбар -->
    <aside class="app-sidebar" id="app-sidebar" aria-label="{config.t("sidebar.aria")}">
      {partial("sidebar_header", config, ctx)}

      <!-- Поиск по сайдбару -->
      <div class="sidebar-search" role="search">
        <div class="search-input-wrapper">
          <label for="sidebar-filter" class="visually-hidden">{config.t("sidebar.filter_label")}</label>
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input type="search" id="sidebar-filter" placeholder="{config.t("sidebar.filter_placeholder")}" autocomplete="off" aria-label="{config.t("sidebar.filter_aria")}">
          <button type="button" class="clear-search-btn" id="clear-filter" title="{config.t("sidebar.filter_clear_title")}" aria-label="{config.t("sidebar.filter_clear_aria")}">&times;</button>
        </div>
      </div>

      <!-- Оглавление сайдбара -->
      <nav class="sidebar-content" id="sidebar-content" aria-label="{config.t("sidebar.content_aria")}"{f' data-rel-root="{rel_root}" data-current="{article.rel_output_path}"' if hybrid else ''}>
        {sidebar_html}
      </nav>

      <footer class="sidebar-footer">
        <span class="catalog-stat">{config.t("sidebar.articles_count")} {'<strong data-nav-count></strong>' if hybrid else f'<strong>{total_articles}</strong>'}</span>
        <span class="sidebar-version">v{version}</span>
      </footer>
    </aside>

    <!-- Ползунок изменения ширины сайдбара (drag-to-resize) -->
    <div class="resizer" id="drag-resizer" role="separator" aria-orientation="vertical" aria-label="{config.t("sidebar.resizer_aria")}" tabindex="0"></div>

    <!-- Основная контентная область -->
    <div class="app-main" id="app-main">
      <header class="content-header">
        <button type="button" class="btn-toggle-sidebar" id="toggle-sidebar" title="{config.t("sidebar.menu_toggle_title")}" aria-label="{config.t("sidebar.menu_toggle_aria")}" aria-expanded="false" aria-controls="app-sidebar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
        </button>
        {breadcrumbs_html}
      </header>

      <main class="content-wrapper" id="main-content">
        <article class="article-body">
          {partial("article_header", config, ctx)}

          <div class="article-markdown">
            {article_html}
          </div>

          <!-- Навигация Предыдущая / Следующая статья -->
          <nav class="article-bottom-nav" aria-label="{config.t("article.nav_aria")}">
            {prev_link_html}
            {next_link_html}
          </nav>
        </article>

        <!-- Оглавление текущей статьи -->
        {toc_html}
      </main>

      {partial("article_footer", config, ctx)}
    </div>
  </div>

  <!-- Полноэкранный модальный просмотр Mermaid диаграмм -->
  <div class="mermaid-modal" id="mermaid-modal" role="dialog" aria-modal="true" aria-labelledby="mermaid-modal-title" aria-hidden="true">
    <div class="modal-backdrop" data-action="close-mermaid-modal" aria-hidden="true"></div>
    <div class="modal-dialog" role="document">
      <header class="modal-header">
        <h2 class="modal-title" id="mermaid-modal-title">{config.t("mermaid.modal_title")}</h2>
        <div class="modal-actions">
          <button type="button" class="btn-modal-action" data-action="zoom-mermaid-in" title="{config.t("mermaid.zoom_in")}" aria-label="{config.t("mermaid.zoom_in")}">+</button>
          <button type="button" class="btn-modal-action" data-action="zoom-mermaid-out" title="{config.t("mermaid.zoom_out")}" aria-label="{config.t("mermaid.zoom_out")}">-</button>
          <button type="button" class="btn-modal-action" data-action="zoom-mermaid-reset" title="{config.t("mermaid.zoom_reset_title")}" aria-label="{config.t("mermaid.zoom_reset_aria")}">1:1</button>
          <button type="button" class="btn-modal-action btn-modal-close" data-action="close-mermaid-modal" title="{config.t("mermaid.close_title")}" aria-label="{config.t("mermaid.close_aria")}">&times;</button>
        </div>
      </header>
      <div class="modal-body" id="mermaid-modal-content" role="region" aria-label="{config.t("mermaid.viewport_aria")}" tabindex="0"></div>
    </div>
  </div>

  <!-- Кнопка Наверх -->
  <button type="button" class="btn-scroll-top" id="btn-scroll-top" title="{config.t("page.scroll_top_title")}" aria-label="{config.t("page.scroll_top_aria")}">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="18 15 12 9 6 15"></polyline></svg>
  </button>

  <!-- Единый плавающий переключатель темы -->
  {theme_switcher_html(config)}

  <!-- Скрипты -->
{vendor_scripts}  <script src="{asset_url(rel_root, 'assets/main.js')}"></script>{extra_asset_tags(config, rel_root, "js")}
</body>
</html>
"""

def render_index_page(
    modules_tree: List[Dict[str, Any]],
    total_articles: int,
    total_mermaid: int,
    version: str,
    config: BookConfig
) -> str:
    """Генерация главной страницы index.html (Интерактивный дашборд и каталог)."""
    rel_root = "./"
    ip = config.index_page
    counts = {"modules": len(modules_tree), "articles": total_articles,
              "articles_grouped": f"{total_articles:,}".replace(",", " "), "mermaid": total_mermaid}
    fc = lambda text: fill_counts(text, counts)
    index_footer_html = "\n      ".join(f"<p>{line}</p>" for line in ip.footer_html)
    stats_html = "\n".join(
        f"""        <div class="stat-box">
          <span class="stat-number">{fc(st['value'])}</span>
          <span class="stat-desc">{fc(st['label'])}</span>
        </div>""" for st in ip.stats)
    steps_html = "\n".join(
        f"""        <li class="roadmap-step">
          <span class="step-badge">{st['badge']}</span>
          <div class="step-content">
            <h4>{st['title_html']}</h4>
            <p>{st['text_html']}</p>
          </div>
        </li>""" for st in ip.roadmap_steps)

    ctx = {
        "hero_badge": fc(ip.hero_badge_html),
        "version": version,
        "hero_title": fc(ip.hero_title_html),
        "quote": ip.quote_html,
        "quote_author": ip.quote_author_html,
        "search_label": config.t("index.search_label"),
        "search_placeholder": html.escape(fc(ip.search_placeholder)),
        "search_aria": config.t("index.search_aria"),
        "search_results_aria": config.t("index.search_results_aria"),
        "stats_aria": config.t("index.stats_aria"),
        "stats": stats_html,
        "footer": index_footer_html,
    }
    load_hooks(config).page_context(None, ctx)

    cards_html = []
    for mod in modules_tree:
        num = mod["num"]
        title = mod["title"]
        m_articles = mod["articles"]
        sub_count = len(mod["subsections"])
        
        all_mod_arts = list(m_articles)
        for s in mod["subsections"]:
            all_mod_arts.extend(s["articles"])

        art_count = len(all_mod_arts)
        mermaid_count = sum(a.mermaid_count for a in all_mod_arts)
        first_art_href = rel_root + all_mod_arts[0].rel_output_path if all_mod_arts else "#"

        cards_html.append(f"""
<li class="module-card">
  <div class="module-card-header">
    <span class="card-num-badge">{num:02d}</span>
    <span class="card-count-badge">{config.t("index.card_articles", n=art_count)}</span>
  </div>
  <h3 class="module-card-title">{html.escape(title)}</h3>
  <div class="module-card-meta">
    <span>{config.t("index.card_mermaid", n=mermaid_count)}</span>
    {f'<span>{config.t("index.card_sections", n=sub_count)}</span>' if sub_count > 0 else f'<span>{config.t("index.card_basic")}</span>'}
  </div>
  <div class="module-card-actions">
    <a href="{first_art_href}" class="btn-card-start">{config.t("index.card_start")}</a>
  </div>
</li>
""")

    return f"""<!DOCTYPE html>
{make_html_tag()}
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{fc(ip.title_html)}</title>
  <meta name="description" content="{fc(ip.meta_description_html)}">
  {render_favicon_links(config, rel_root)}
  {make_anti_flicker_script(config)}
  <link rel="stylesheet" href="{asset_url(rel_root, 'assets/style.css')}">{extra_asset_tags(config, rel_root, "css")}
</head>
<body class="index-page">
  <main class="index-container" id="main-content">
    <!-- Героическая секция -->
    {partial("index_hero", config, ctx)}

    <!-- Каталог модулей -->
    <section class="modules-catalog" aria-labelledby="catalog-heading">
      <header class="catalog-header">
        <h2 class="section-title" id="catalog-heading">{fc(ip.catalog_title_html)}</h2>
        <p class="section-sub">{fc(ip.catalog_sub_html)}</p>
      </header>

      <ul class="modules-grid">
        {"".join(cards_html)}
      </ul>
    </section>

    <!-- Дорожная карта обучения -->
    <section class="learning-roadmap" aria-labelledby="roadmap-heading">
      <header class="roadmap-header">
        <h2 class="section-title" id="roadmap-heading">{fc(ip.roadmap_title_html)}</h2>
      </header>
      <ol class="roadmap-timeline">
{steps_html}
      </ol>
    </section>

    {partial("index_footer", config, ctx)}
  </main>

  <!-- Единый плавающий переключатель темы -->
  {theme_switcher_html(config)}

  <script src="{asset_url(rel_root, 'assets/search-data.js')}"></script>
  <script src="{asset_url(rel_root, 'assets/main.js')}"></script>{extra_asset_tags(config, rel_root, "js")}
</body>
</html>
"""
