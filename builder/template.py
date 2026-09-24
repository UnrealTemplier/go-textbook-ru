"""
builder/template.py
HTML5 шаблоны, CSS стили в стиле Go Workout (Dark Theme) и JS скрипты для
автономной работы портала (file:/// и веб-хостинг).
"""

import os
import re
import html
from typing import Dict, Any, List, Optional
from builder.scanner import Article

def get_project_version(agents_path: Optional[str] = None) -> str:
    """
    Считывание и строгая валидация версии проекта из AGENTS.md.
    AGENTS.md является единственным источником правды для версии проекта (SemVer MAJOR.MINOR.PATCH).
    """
    if not agents_path:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        agents_path = os.path.join(repo_root, "AGENTS.md")

    if not os.path.isfile(agents_path):
        raise FileNotFoundError(f"[VERSION ERROR] Canonical version file not found: {agents_path}")

    with open(agents_path, "r", encoding="utf-8") as fp:
        content = fp.read()

    pattern = re.compile(
        r"^\s*[-*]?\s*\*\*Current project version:\*\*\s*`?([0-9A-Za-z.-]+)`?",
        re.MULTILINE
    )
    matches = list(pattern.finditer(content))

    if len(matches) == 0:
        raise ValueError(
            f"[VERSION ERROR] Project version definition not found in {agents_path}. "
            "Expected entry such as: '* **Current project version:** `1.1.0`'"
        )

    if len(matches) > 1:
        raise ValueError(
            f"[VERSION ERROR] Multiple canonical version declarations found in {agents_path} ({len(matches)} occurrences). "
            "Exactly one canonical version declaration is allowed to prevent desynchronization."
        )

    version_raw = matches[0].group(1).strip()

    semver_pattern = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
    if not semver_pattern.match(version_raw):
        raise ValueError(
            f"[VERSION ERROR] Invalid project version format '{version_raw}' found in {agents_path}. "
            "Version must strictly comply with semantic versioning (MAJOR.MINOR.PATCH, e.g. 1.1.0)."
        )

    return version_raw

GO_LOGO_SVG = (
    '<svg class="logo-go-icon" viewBox="0 42 165 82" fill="#00ADD8" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<g transform="translate(9, 46)" fill="#00ADD8" fill-rule="evenodd">'
    '<path d="m74.1 22.3c-6.3 1.6-10.6 2.8-16.8 4.4-1.5.4-1.6.5-2.9-1-1.5-1.7-2.6-2.8-4.7-3.8-6.3-3.1-12.4-2.2-18.1 1.5-6.8 4.4-10.3 10.9-10.2 19 .1 8 5.6 14.6 13.5 15.7 6.8.9 12.5-1.5 17-6.6.9-1.1 1.7-2.3 2.7-3.7-3.6 0-8.1 0-19.3 0-2.1 0-2.6-1.3-1.9-3 1.3-3.1 3.7-8.3 5.1-10.9.3-.6 1-1.6 2.5-1.6h36.4c-.2 2.7-.2 5.4-.6 8.1-1.1 7.2-3.8 13.8-8.2 19.6-7.2 9.5-16.6 15.4-28.5 17-9.8 1.3-18.9-.6-26.9-6.6-7.4-5.6-11.6-13-12.7-22.2-1.3-10.9 1.9-20.7 8.5-29.3 7.1-9.3 16.5-15.2 28-17.3 9.4-1.7 18.4-.6 26.5 4.9 5.3 3.5 9.1 8.3 11.6 14.1.6.9.2 1.4-1 1.7z"/>'
    '<path d="m107.2 77.6c-9.1-.2-17.4-2.8-24.4-8.8-5.9-5.1-9.6-11.6-10.8-19.3-1.8-11.3 1.3-21.3 8.1-30.2 7.3-9.6 16.1-14.6 28-16.7 10.2-1.8 19.8-.8 28.5 5.1 7.9 5.4 12.8 12.7 14.1 22.3 1.7 13.5-2.2 24.5-11.5 33.9-6.6 6.7-14.7 10.9-24 12.8-2.7.5-5.4.6-8 .9zm23.8-40.4c-.1-1.3-.1-2.3-.3-3.3-1.8-9.9-10.9-15.5-20.4-13.3-9.3 2.1-15.3 8-17.5 17.4-1.8 7.8 2 15.7 9.2 18.9 5.5 2.4 11 2.1 16.3-.6 7.9-4.1 12.2-10.5 12.7-19.1z" fill-rule="nonzero"/>'
    '</g>'
    '</svg>'
)

ANTI_FLICKER_SCRIPT = (
    '<script>/* Theme & Retro anti-flicker */(function(){'
    'try{'
    "var d=document.documentElement;"
    "var t=localStorage.getItem('go_encyclopedia_theme');"
    "if(t&&['paper','light','dark'].includes(t)){d.dataset.theme=t;}else{d.dataset.theme='dark';}"
    "var r=localStorage.getItem('go_encyclopedia_retro_effects');"
    "if(r){"
    "var c=JSON.parse(r);"
    "var s=d.style;"
    "if(c.trail&&c.trail.enabled){var ts=(c.trail.strength!==undefined)?c.trail.strength:100;if(ts>0){d.dataset.retroTrail='on';s.setProperty('--retro-trail',(ts/100).toFixed(2));}}"
    "if(c.site){"
    "if(c.site.vhs&&c.site.vhs.enabled){d.dataset.siteVhs='on';s.setProperty('--retro-site-vhs',((c.site.vhs.strength||0)/100).toFixed(2));}"
    "if(c.site.crt&&c.site.crt.enabled){d.dataset.siteCrt='on';s.setProperty('--retro-site-crt',((c.site.crt.strength||0)/100).toFixed(2));}"
    "if(c.site.noise&&c.site.noise.enabled){d.dataset.siteNoise='on';s.setProperty('--retro-site-noise',((c.site.noise.strength||0)/100).toFixed(2));}"
    "}"
    "if(c.code){"
    "if(c.code.vhs&&c.code.vhs.enabled){d.dataset.codeVhs='on';s.setProperty('--retro-code-vhs',((c.code.vhs.strength||0)/100).toFixed(2));}"
    "if(c.code.crt&&c.code.crt.enabled){d.dataset.codeCrt='on';s.setProperty('--retro-code-crt',((c.code.crt.strength||0)/100).toFixed(2));}"
    "if(c.code.noise&&c.code.noise.enabled){d.dataset.codeNoise='on';s.setProperty('--retro-code-noise',((c.code.noise.strength||0)/100).toFixed(2));}"
    "}"
    "}"
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

RETRO_SITE_EFFECTS_HTML = (
    '<div id="retro-site-effects" class="retro-site-effects" aria-hidden="true">\n'
    '  <div class="retro-site-vhs-layer"></div>\n'
    '  <div class="retro-site-crt-layer"></div>\n'
    '  <div class="retro-site-noise-layer"></div>\n'
    '</div>\n'
    '<div id="retro-phosphor-trail" class="retro-phosphor-trail" aria-hidden="true">\n'
    '  <div class="retro-phosphor-beam"></div>\n'
    '</div>'
)

RETRO_CONTROLS_HTML = (
    '<button type="button" id="retro-btn" class="floating-retro-btn" '
    'aria-label="Ретро-эффекты" aria-haspopup="dialog" aria-expanded="false" aria-controls="retro-popover">\n'
    '  <svg class="retro-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">\n'
    '    <line x1="4" y1="21" x2="4" y2="14"></line>\n'
    '    <line x1="4" y1="10" x2="4" y2="3"></line>\n'
    '    <line x1="12" y1="21" x2="12" y2="12"></line>\n'
    '    <line x1="12" y1="8" x2="12" y2="3"></line>\n'
    '    <line x1="20" y1="21" x2="20" y2="16"></line>\n'
    '    <line x1="20" y1="12" x2="20" y2="3"></line>\n'
    '    <line x1="1" y1="14" x2="7" y2="14"></line>\n'
    '    <line x1="9" y1="8" x2="15" y2="8"></line>\n'
    '    <line x1="17" y1="16" x2="23" y2="16"></line>\n'
    '  </svg>\n'
    '</button>\n'
    '<div id="retro-popover" class="retro-popover" role="dialog" aria-label="Ретро-эффекты" aria-hidden="true">\n'
    '  <header class="retro-popover-header">\n'
    '    <div class="retro-popover-title">\n'
    '      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">\n'
    '        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>\n'
    '        <line x1="8" y1="21" x2="16" y2="21"></line>\n'
    '        <line x1="12" y1="17" x2="12" y2="21"></line>\n'
    '      </svg>\n'
    '      <span>Ретро-эффекты</span>\n'
    '    </div>\n'
    '    <button type="button" class="btn-retro-close" id="retro-close-btn" aria-label="Закрыть настройки ретро-эффектов">&times;</button>\n'
    '  </header>\n'
    '  <div class="retro-popover-body">\n'
    '    <div class="retro-trail-card" data-scope="trail">\n'
    '      <label class="retro-switch" for="retro-trail-toggle">\n'
    '        <input type="checkbox" id="retro-trail-toggle" data-scope="trail">\n'
    '        <span class="retro-switch-slider"></span>\n'
    '        <span class="retro-switch-label">Phosphor trail</span>\n'
    '      </label>\n'
    '      <div class="retro-slider-wrap" id="retro-trail-slider-wrap">\n'
    '        <input type="range" class="retro-slider" id="retro-trail-slider" data-scope="trail" min="0" max="100" step="1" value="100" aria-label="Сила Phosphor trail">\n'
    '        <span class="retro-slider-val" id="retro-trail-val">100%</span>\n'
    '      </div>\n'
    '    </div>\n'
    '    <fieldset class="retro-group">\n'
    '      <legend class="retro-group-legend">Весь сайт</legend>\n'
    '      <div class="retro-control-row" data-scope="site" data-effect="vhs">\n'
    '        <label class="retro-switch" for="retro-site-vhs-toggle">\n'
    '          <input type="checkbox" id="retro-site-vhs-toggle" data-scope="site" data-effect="vhs">\n'
    '          <span class="retro-switch-slider"></span>\n'
    '          <span class="retro-switch-label">VHS / Scanlines</span>\n'
    '        </label>\n'
    '        <div class="retro-slider-wrap" id="retro-site-vhs-slider-wrap">\n'
    '          <input type="range" class="retro-slider" id="retro-site-vhs-slider" data-scope="site" data-effect="vhs" min="0" max="100" step="1" value="30" aria-label="Сила VHS для всего сайта">\n'
    '          <span class="retro-slider-val" id="retro-site-vhs-val">30%</span>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="retro-control-row" data-scope="site" data-effect="crt">\n'
    '        <label class="retro-switch" for="retro-site-crt-toggle">\n'
    '          <input type="checkbox" id="retro-site-crt-toggle" data-scope="site" data-effect="crt">\n'
    '          <span class="retro-switch-slider"></span>\n'
    '          <span class="retro-switch-label">CRT</span>\n'
    '        </label>\n'
    '        <div class="retro-slider-wrap" id="retro-site-crt-slider-wrap">\n'
    '          <input type="range" class="retro-slider" id="retro-site-crt-slider" data-scope="site" data-effect="crt" min="0" max="100" step="1" value="30" aria-label="Сила CRT для всего сайта">\n'
    '          <span class="retro-slider-val" id="retro-site-crt-val">30%</span>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="retro-control-row" data-scope="site" data-effect="noise">\n'
    '        <label class="retro-switch" for="retro-site-noise-toggle">\n'
    '          <input type="checkbox" id="retro-site-noise-toggle" data-scope="site" data-effect="noise">\n'
    '          <span class="retro-switch-slider"></span>\n'
    '          <span class="retro-switch-label">Noise</span>\n'
    '        </label>\n'
    '        <div class="retro-slider-wrap" id="retro-site-noise-slider-wrap">\n'
    '          <input type="range" class="retro-slider" id="retro-site-noise-slider" data-scope="site" data-effect="noise" min="0" max="100" step="1" value="20" aria-label="Сила Noise для всего сайта">\n'
    '          <span class="retro-slider-val" id="retro-site-noise-val">20%</span>\n'
    '        </div>\n'
    '      </div>\n'
    '    </fieldset>\n'
    '    <fieldset class="retro-group">\n'
    '      <legend class="retro-group-legend">Блоки кода</legend>\n'
    '      <div class="retro-control-row" data-scope="code" data-effect="vhs">\n'
    '        <label class="retro-switch" for="retro-code-vhs-toggle">\n'
    '          <input type="checkbox" id="retro-code-vhs-toggle" data-scope="code" data-effect="vhs">\n'
    '          <span class="retro-switch-slider"></span>\n'
    '          <span class="retro-switch-label">VHS / Scanlines</span>\n'
    '        </label>\n'
    '        <div class="retro-slider-wrap" id="retro-code-vhs-slider-wrap">\n'
    '          <input type="range" class="retro-slider" id="retro-code-vhs-slider" data-scope="code" data-effect="vhs" min="0" max="100" step="1" value="30" aria-label="Сила VHS для блоков кода">\n'
    '          <span class="retro-slider-val" id="retro-code-vhs-val">30%</span>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="retro-control-row" data-scope="code" data-effect="crt">\n'
    '        <label class="retro-switch" for="retro-code-crt-toggle">\n'
    '          <input type="checkbox" id="retro-code-crt-toggle" data-scope="code" data-effect="crt">\n'
    '          <span class="retro-switch-slider"></span>\n'
    '          <span class="retro-switch-label">CRT</span>\n'
    '        </label>\n'
    '        <div class="retro-slider-wrap" id="retro-code-crt-slider-wrap">\n'
    '          <input type="range" class="retro-slider" id="retro-code-crt-slider" data-scope="code" data-effect="crt" min="0" max="100" step="1" value="40" aria-label="Сила CRT для блоков кода">\n'
    '          <span class="retro-slider-val" id="retro-code-crt-val">40%</span>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="retro-control-row" data-scope="code" data-effect="noise">\n'
    '        <label class="retro-switch" for="retro-code-noise-toggle">\n'
    '          <input type="checkbox" id="retro-code-noise-toggle" data-scope="code" data-effect="noise">\n'
    '          <span class="retro-switch-slider"></span>\n'
    '          <span class="retro-switch-label">Noise</span>\n'
    '        </label>\n'
    '        <div class="retro-slider-wrap" id="retro-code-noise-slider-wrap">\n'
    '          <input type="range" class="retro-slider" id="retro-code-noise-slider" data-scope="code" data-effect="noise" min="0" max="100" step="1" value="20" aria-label="Сила Noise для блоков кода">\n'
    '          <span class="retro-slider-val" id="retro-code-noise-val">20%</span>\n'
    '        </div>\n'
    '      </div>\n'
    '    </fieldset>\n'
    '  </div>\n'
    '</div>'
)

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
    total_articles: int = 1413,
    version: Optional[str] = None
) -> str:
    """Генерация полной HTML-страницы статьи."""
    if not version:
        version = get_project_version()
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

    reading_time = max(2, int(article.size_bytes / 800))

    return f"""<!DOCTYPE html>
<html lang="ru" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(article.title)} | Инженерная энциклопедия бэкенда</title>
  <meta name="description" content="Полное руководство: {html.escape(article.title)}. Go, архитектура систем, computer science.">
  <link rel="icon" href="{rel_root}favicon.ico" sizes="32x32">
  <link rel="icon" type="image/svg+xml" href="{rel_root}favicon.svg" sizes="any">
  {ANTI_FLICKER_SCRIPT}
  <link rel="stylesheet" href="{rel_root}assets/style.css">
  <link rel="stylesheet" href="{rel_root}assets/vendor/katex/katex.min.css">
</head>
<body>
  <div class="reading-progress-bar" id="reading-progress" role="progressbar" aria-label="Прогресс чтения статьи" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>

  <div class="app-layout">
    <!-- Левый сайдбар -->
    <aside class="app-sidebar" id="app-sidebar" aria-label="Навигация по курсу">
      <header class="sidebar-header">
        <a href="{rel_root}index.html" class="brand-logo" aria-label="На главную: Go Backend Энциклопедия">
          <div class="logo-icon" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
          </div>
          <div class="logo-text">
            <span class="logo-title">{GO_LOGO_SVG} BACKEND</span>
            <span class="logo-sub">Энциклопедия</span>
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
        <p>Инженерная веб-энциклопедия бэкенда и языка Go • Авторский стиль Брайана Кернигана</p>
        <p>Собрано автономным генератором без внешних зависимостей. 100% Offline Ready.</p>
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

  <!-- Плавающие элементы ретро-эффектов -->
  {RETRO_SITE_EFFECTS_HTML}
  {RETRO_CONTROLS_HTML}

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
    version: Optional[str] = None
) -> str:
    """Генерация главной страницы index.html (Интерактивный дашборд и каталог)."""
    if not version:
        version = get_project_version()
    rel_root = "./"

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
<html lang="ru" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Инженерная веб-энциклопедия бэкенда (Go &amp; Computer Science)</title>
  <meta name="description" content="Фундаментальная энциклопедия бэкенда, распределенных систем и языка Go от Брайана Кернигана. 1 400+ статей, 1 400+ схем Mermaid.">
  <link rel="icon" href="{rel_root}favicon.ico" sizes="32x32">
  <link rel="icon" type="image/svg+xml" href="{rel_root}favicon.svg" sizes="any">
  {ANTI_FLICKER_SCRIPT}
  <link rel="stylesheet" href="{rel_root}assets/style.css">
</head>
<body class="index-page">
  <main class="index-container" id="main-content">
    <!-- Героическая секция -->
    <header class="index-hero">
      <div class="hero-top-meta">
        <span class="hero-badge">Энциклопедия Computer Science &amp; Backend</span>
        <span class="hero-version">v{version}</span>
      </div>
      <h1 class="hero-title">Фундаментальный бэкенд на Go: от кремния до распределенных систем</h1>
      <blockquote class="hero-quote">
        <p><em>«Управление сложностью — вот суть программирования».</em></p>
        <cite class="quote-author">— Брайан Керниган</cite>
      </blockquote>

      <!-- Полнотекстовый живой поиск -->
      <div class="hero-search-box" role="search">
        <div class="search-bar-inner">
          <label for="global-search-input" class="visually-hidden">Поиск по лекциям</label>
          <svg class="hero-search-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input type="search" id="global-search-input" placeholder="Поиск по 1 413 лекциям (например: netpoller, GC, MVCC, Raft, CAS)..." autocomplete="off" aria-label="Поиск по лекциям">
        </div>
        <div class="search-results-dropdown" id="global-search-results" role="listbox" aria-label="Результаты поиска"></div>
      </div>

      <!-- Виджеты статистики -->
      <div class="stats-ribbon" role="region" aria-label="Статистика курса">
        <div class="stat-box">
          <span class="stat-number">22</span>
          <span class="stat-desc">Тематических модуля</span>
        </div>
        <div class="stat-box">
          <span class="stat-number">{total_articles}</span>
          <span class="stat-desc">Инженерных лекций</span>
        </div>
        <div class="stat-box">
          <span class="stat-number">{total_mermaid}</span>
          <span class="stat-desc">Диаграмм Mermaid</span>
        </div>
        <div class="stat-box">
          <span class="stat-number">100%</span>
          <span class="stat-desc">Offline &amp; file:///</span>
        </div>
      </div>
    </header>

    <!-- Каталог модулей -->
    <section class="modules-catalog" aria-labelledby="catalog-heading">
      <header class="catalog-header">
        <h2 class="section-title" id="catalog-heading">Каталог учебных модулей</h2>
        <p class="section-sub">22 всеобъемлющих курса, выстроенных в строгую логическую последовательность</p>
      </header>

      <ul class="modules-grid">
        {"".join(cards_html)}
      </ul>
    </section>

    <!-- Дорожная карта обучения -->
    <section class="learning-roadmap" aria-labelledby="roadmap-heading">
      <header class="roadmap-header">
        <h2 class="section-title" id="roadmap-heading">Инженерный трек: как изучать базу</h2>
      </header>
      <ol class="roadmap-timeline">
        <li class="roadmap-step">
          <span class="step-badge">Шаг 1</span>
          <div class="step-content">
            <h4>Кремний и Операционная система (Модули 1–3)</h4>
            <p>Логические вентили, регистры, конвейеры CPU, кэш-линии, виртуальная память, CFS, epoll и сокеты. Без этого понимание рантайма Go невозможно.</p>
          </div>
        </li>
        <li class="roadmap-step">
          <span class="step-badge">Шаг 2</span>
          <div class="step-content">
            <h4>Глубокий Go и Runtime (Модули 4–9)</h4>
            <p>GMP-планировщик, стек горутины, аллокатор mheap, сборщик мусора тройной раскраски, сетевой поллер (netpoller) и архитектура сервисов.</p>
          </div>
        </li>
        <li class="roadmap-step">
          <span class="step-badge">Шаг 3</span>
          <div class="step-content">
            <h4>Хранилища и Распределенные системы (Модули 10–14)</h4>
            <p>B+ Tree vs LSM, MVCC, транзакции, Kafka, NATS, консенсус Raft/Paxos, CAP/PACELC и микросервисы.</p>
          </div>
        </li>
        <li class="roadmap-step">
          <span class="step-badge">Шаг 4</span>
          <div class="step-content">
            <h4>Надежность, Performance &amp; DSA (Модули 15–22)</h4>
            <p>Профилирование pprof, trace, AppSec, алгоритмы, 218 задач LeetCode и глубокая подготовка к BigTech интервью.</p>
          </div>
        </li>
      </ol>
    </section>

    <footer class="index-footer">
      <p>Инженерная веб-энциклопедия бэкенда и языка Go • В память о традициях Bell Labs и Брайана Кернигана</p>
      <p>Полностью автономная сборка. Никаких трекеров, рекламы и внешних серверов.</p>
    </footer>
  </main>

  <!-- Единый плавающий переключатель темы -->
  {FLOATING_THEME_SWITCHER_HTML}

  <!-- Плавающие элементы ретро-эффектов -->
  {RETRO_SITE_EFFECTS_HTML}
  {RETRO_CONTROLS_HTML}

  <script src="{rel_root}assets/search-data.js"></script>
  <script src="{rel_root}assets/main.js"></script>
</body>
</html>
"""
