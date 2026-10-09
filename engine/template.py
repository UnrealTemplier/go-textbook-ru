"""
engine/template.py
HTML5 шаблоны, CSS стили в стиле Go Workout (Dark Theme) и JS скрипты для
автономной работы портала (file:/// и веб-хостинг).
"""

import os
import re
import html
import json
from typing import Dict, Any, List, Optional
from .config import BookConfig, read_text_asset
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

def make_anti_flicker_script(config: BookConfig) -> str:
    """Генерирует anti-flicker инлайн-скрипт с динамическим списком тем из manifest.json."""
    default_theme, themes = _load_themes_manifest()
    theme_keys = [t["key"] for t in themes]
    theme_keys_js = str(theme_keys).replace("'", "'")
    return (
        '<script>/* Theme anti-flicker */(function(){'
        'try{'
        "var d=document.documentElement;"
        f"var t=localStorage.getItem('{config.storage_key('theme')}');"
        f"if(t&&{theme_keys_js}.includes(t)){{d.dataset.theme=t;}}else{{d.dataset.theme='{default_theme}';}}"
        "}catch(e){}"
        '})();</script>'
    )

FLOATING_THEME_SWITCHER_HTML = (
    '<button type="button" id="theme-switcher-btn" class="floating-theme-switcher" '
    'data-action="toggle-theme" '
    'aria-label="Текущая тема: Dark (нажмите для смены)">\n'
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

def render_sidebar(
    modules_tree: List[Dict[str, Any]],
    current_article: Optional[Article],
    rel_root: str
) -> str:
    """Генерация интерактивного сайдбара с древовидным аккордеоном."""
    html_parts = []
    html_parts.append('<div class="sidebar-nav">')

    curr_path = current_article.rel_output_path if current_article else ""

    for mod in modules_tree:
        mod_num = mod["num"]
        mod_title = mod["title"]
        mod_raw = mod["raw_name"]
        
        # Проверяем, активен ли текущий модуль
        is_mod_active = False
        if current_article and current_article.module_num == mod_num:
            is_mod_active = True

        open_attr = "open" if is_mod_active else ""
        active_class = "active-module" if is_mod_active else ""

        html_parts.append(f'<details class="nav-module {active_class}" {open_attr}>')
        html_parts.append(f'<summary class="nav-module-title"><span class="mod-badge">{mod_num}</span> <span class="mod-text">{html.escape(mod_title)}</span></summary>')
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
            html_parts.append(f'<summary class="nav-submodule-title"><span class="sub-chevron" aria-hidden="true"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"></polyline></svg></span><span class="sub-text">{html.escape(sub_name)}</span></summary>')
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

def render_breadcrumbs(article: Article, rel_root: str) -> str:
    """Хлебные крошки над статьей."""
    crumbs = [
        f'<li class="crumb-item"><a href="{rel_root}index.html" class="crumb-link">Главная</a></li>'
    ]
    crumbs.append('<li class="crumb-sep" aria-hidden="true">/</li>')
    crumbs.append(f'<li class="crumb-item crumb-module">{html.escape(article.module_name)}</li>')
    
    if article.subsection_name:
        crumbs.append('<li class="crumb-sep" aria-hidden="true">/</li>')
        crumbs.append(f'<li class="crumb-item crumb-sub">{html.escape(article.subsection_name)}</li>')

    crumbs.append('<li class="crumb-sep" aria-hidden="true">/</li>')
    crumbs.append(f'<li class="crumb-item crumb-current" aria-current="page">{html.escape(article.title)}</li>')

    return f'<nav class="breadcrumbs" aria-label="Хлебные крошки"><ol class="breadcrumbs-list">{" ".join(crumbs)}</ol></nav>'

def render_article_page(
    article: Article,
    article_html: str,
    toc: List[Dict[str, Any]],
    modules_tree: List[Dict[str, Any]],
    total_articles: int,
    version: str,
    config: BookConfig
) -> str:
    """Генерация полной HTML-страницы статьи."""
    rel_root = get_rel_root(article.rel_output_path)
    sidebar_html = render_sidebar(modules_tree, article, rel_root)
    breadcrumbs_html = render_breadcrumbs(article, rel_root)

    # Предыдущая и следующая статья
    prev_link_html = ""
    if article.prev_article:
        p_href = rel_root + article.prev_article.rel_output_path
        prev_link_html = f"""
<a href="{p_href}" class="article-nav-card prev-card" rel="prev">
  <span class="nav-dir">← Предыдущая статья</span>
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
  <span class="nav-dir">Следующая статья →</span>
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
<aside class="article-toc" id="article-toc" aria-label="Оглавление страницы">
  <header class="toc-header">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
    <span>На этой странице</span>
  </header>
  <ul class="toc-list">
    {"".join(toc_items)}
  </ul>
</aside>
"""
    else:
        toc_html = ""

    ap = config.article_page
    br = config.branding
    footer_html = "\n        ".join(f"<p>{line}</p>" for line in ap.footer_html)
    rt = config.navigation.reading_time
    reading_time = max(rt.min, int(article.size_bytes / rt.divisor))

    return f"""<!DOCTYPE html>
{make_html_tag()}
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(article.title)}{ap.title_suffix_html}</title>
  <meta name="description" content="{ap.meta_description_html.replace('{title}', html.escape(article.title))}">
  {render_favicon_links(config, rel_root)}
  {make_anti_flicker_script(config)}
  <link rel="stylesheet" href="{rel_root}assets/style.css">
  <link rel="stylesheet" href="{rel_root}assets/vendor/katex/katex.min.css">
</head>
<body>
  <div class="reading-progress-bar" id="reading-progress" role="progressbar" aria-label="Прогресс чтения статьи" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>

  <div class="app-layout">
    <!-- Левый сайдбар -->
    <aside class="app-sidebar" id="app-sidebar" aria-label="Навигация по курсу">
      <header class="sidebar-header">
        <a href="{rel_root}index.html" class="brand-logo" aria-label="{br.logo_aria_label}">
          <div class="logo-icon" aria-hidden="true">
            {read_text_asset(config, br.logo_icon_svg_file)}
          </div>
          <div class="logo-text">
            <span class="logo-title">{read_text_asset(config, br.logo_title_svg_file)}{br.logo_title_text}</span>
            <span class="logo-sub">{br.logo_sub}</span>
          </div>
        </a>
      </header>

      <!-- Поиск по сайдбару -->
      <div class="sidebar-search" role="search">
        <div class="search-input-wrapper">
          <label for="sidebar-filter" class="visually-hidden">Фильтр по лекциям</label>
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input type="search" id="sidebar-filter" placeholder="Фильтр по лекциям..." autocomplete="off" aria-label="Фильтр по лекциям">
          <button type="button" class="clear-search-btn" id="clear-filter" title="Очистить" aria-label="Очистить фильтр">&times;</button>
        </div>
      </div>

      <!-- Оглавление сайдбара -->
      <nav class="sidebar-content" id="sidebar-content" aria-label="Содержание учебника">
        {sidebar_html}
      </nav>

      <footer class="sidebar-footer">
        <span class="catalog-stat">Статей: <strong>{total_articles}</strong></span>
        <span class="sidebar-version">v{version}</span>
      </footer>
    </aside>

    <!-- Ползунок изменения ширины сайдбара (drag-to-resize) -->
    <div class="resizer" id="drag-resizer" role="separator" aria-orientation="vertical" aria-label="Регулятор ширины боковой панели" tabindex="0"></div>

    <!-- Основная контентная область -->
    <div class="app-main" id="app-main">
      <header class="content-header">
        <button type="button" class="btn-toggle-sidebar" id="toggle-sidebar" title="Открыть меню" aria-label="Открыть или закрыть боковое меню" aria-expanded="false" aria-controls="app-sidebar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
        </button>
        {breadcrumbs_html}
      </header>

      <main class="content-wrapper" id="main-content">
        <article class="article-body">
          <header class="article-header">
            <div class="article-meta-tags">
              <span class="meta-tag module-tag">Модуль {article.module_num}</span>
              <span class="meta-tag read-time">⏱ ~{reading_time} мин чтения</span>
              {f'<span class="meta-tag mermaid-tag">📐 {article.mermaid_count} Mermaid диаграмм</span>' if article.mermaid_count > 0 else ''}
            </div>
            <h1 class="article-title">{html.escape(article.title)}</h1>
          </header>

          <div class="article-markdown">
            {article_html}
          </div>

          <!-- Навигация Предыдущая / Следующая статья -->
          <nav class="article-bottom-nav" aria-label="Навигация по статьям">
            {prev_link_html}
            {next_link_html}
          </nav>
        </article>

        <!-- Оглавление текущей статьи -->
        {toc_html}
      </main>

      <footer class="app-footer">
        {footer_html}
      </footer>
    </div>
  </div>

  <!-- Полноэкранный модальный просмотр Mermaid диаграмм -->
  <div class="mermaid-modal" id="mermaid-modal" role="dialog" aria-modal="true" aria-labelledby="mermaid-modal-title" aria-hidden="true">
    <div class="modal-backdrop" data-action="close-mermaid-modal" aria-hidden="true"></div>
    <div class="modal-dialog" role="document">
      <header class="modal-header">
        <h2 class="modal-title" id="mermaid-modal-title">Архитектурная схема (Mermaid)</h2>
        <div class="modal-actions">
          <button type="button" class="btn-modal-action" data-action="zoom-mermaid-in" title="Приблизить" aria-label="Приблизить">+</button>
          <button type="button" class="btn-modal-action" data-action="zoom-mermaid-out" title="Отдалить" aria-label="Отдалить">-</button>
          <button type="button" class="btn-modal-action" data-action="zoom-mermaid-reset" title="Масштаб 100%" aria-label="Сбросить масштаб 100%">1:1</button>
          <button type="button" class="btn-modal-action btn-modal-close" data-action="close-mermaid-modal" title="Закрыть (Esc)" aria-label="Закрыть модальное окно">&times;</button>
        </div>
      </header>
      <div class="modal-body" id="mermaid-modal-content" role="region" aria-label="Область просмотра диаграммы" tabindex="0"></div>
    </div>
  </div>

  <!-- Кнопка Наверх -->
  <button type="button" class="btn-scroll-top" id="btn-scroll-top" title="Наверх" aria-label="Наверх страницы">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="18 15 12 9 6 15"></polyline></svg>
  </button>

  <!-- Единый плавающий переключатель темы -->
  {FLOATING_THEME_SWITCHER_HTML}

  <!-- Скрипты -->
  <script src="{rel_root}assets/vendor/prism-bundle.min.js"></script>
  <script src="{rel_root}assets/vendor/mermaid.min.js"></script>
  <script src="{rel_root}assets/vendor/katex/katex.min.js"></script>
  <script src="{rel_root}assets/vendor/katex/contrib/auto-render.min.js"></script>
  <script src="{rel_root}assets/main.js"></script>
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
    <span class="card-count-badge">{art_count} статей</span>
  </div>
  <h3 class="module-card-title">{html.escape(title)}</h3>
  <div class="module-card-meta">
    <span>📐 {mermaid_count} схем</span>
    {f'<span>📁 {sub_count} тем</span>' if sub_count > 0 else '<span>📖 Базовый курс</span>'}
  </div>
  <div class="module-card-actions">
    <a href="{first_art_href}" class="btn-card-start">Начать изучение →</a>
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
  <link rel="stylesheet" href="{rel_root}assets/style.css">
</head>
<body class="index-page">
  <main class="index-container" id="main-content">
    <!-- Героическая секция -->
    <header class="index-hero">
      <div class="hero-top-meta">
        <span class="hero-badge">{fc(ip.hero_badge_html)}</span>
        <span class="hero-version">v{version}</span>
      </div>
      <h1 class="hero-title">{fc(ip.hero_title_html)}</h1>
      <blockquote class="hero-quote">
        <p>{ip.quote_html}</p>
        <cite class="quote-author">{ip.quote_author_html}</cite>
      </blockquote>

      <!-- Полнотекстовый живой поиск -->
      <div class="hero-search-box" role="search">
        <div class="search-bar-inner">
          <label for="global-search-input" class="visually-hidden">Поиск по лекциям</label>
          <svg class="hero-search-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input type="search" id="global-search-input" placeholder="{html.escape(fc(ip.search_placeholder))}" autocomplete="off" aria-label="Поиск по лекциям">
        </div>
        <div class="search-results-dropdown" id="global-search-results" role="listbox" aria-label="Результаты поиска"></div>
      </div>

      <!-- Виджеты статистики -->
      <div class="stats-ribbon" role="region" aria-label="Статистика курса">
{stats_html}
      </div>
    </header>

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

    <footer class="index-footer">
      {index_footer_html}
    </footer>
  </main>

  <!-- Единый плавающий переключатель темы -->
  {FLOATING_THEME_SWITCHER_HTML}

  <script src="{rel_root}assets/search-data.js"></script>
  <script src="{rel_root}assets/main.js"></script>
</body>
</html>
"""
