"""
engine/build.py
Главный сборочный конвейер: python -m engine.build [--all | --pilot | --module N | --limit N].
"""

import os
import shutil
import time
import json
import argparse
from pathlib import Path
from typing import List, Optional

from .scanner import KnowledgeBaseScanner, Article
from .media import library_for, credits_page_html
from .converter import MarkdownConverter
from .checksums import verify as verify_checksums
from .config import BookConfig, load_config
from .template import (render_article_page, render_index_page, get_book_version, set_asset_versions,
                       VERSIONED_ASSETS)

# Ассеты изображений ([media]): копируются только у книг с media.enabled, иначе dist/ книги не меняется
MEDIA_ASSETS = ("media.css", "media.js")

def copy_assets(engine_assets_dir: str, dist_assets_dir: str):
    """Копирование статических ассетов (CSS, JS, Vendor) в dist/assets/."""
    os.makedirs(dist_assets_dir, exist_ok=True)
    if not os.path.exists(engine_assets_dir):
        print(f"[WARN] Engine assets directory not found: {engine_assets_dir}")
        return

    for root, dirs, files in os.walk(engine_assets_dir):
        # Пропускаем папку themes/ — она обрабатывается build_themed_css
        dirs[:] = [d for d in dirs if d != "themes"]
        rel = os.path.relpath(root, engine_assets_dir)
        target_dir = os.path.join(dist_assets_dir, rel) if rel != "." else dist_assets_dir
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            # style.css обрабатывается build_themed_css; ассеты [media] — copy_media_assets
            if f == "style.css" or (rel == "." and f in MEDIA_ASSETS):
                continue
            src_f = os.path.join(root, f)
            dst_f = os.path.join(target_dir, f)
            shutil.copy2(src_f, dst_f)

def build_themed_css(engine_assets_dir: str, dist_assets_dir: str) -> list:
    """
    Читает manifest.json из themes/, конкатенирует CSS файлы тем
    с основным style.css и записывает итоговый style.css в dist/assets/.
    Возвращает список словарей всех тем манифеста.
    """
    themes_dir = os.path.join(engine_assets_dir, "themes")
    manifest_path = os.path.join(themes_dir, "manifest.json")

    if not os.path.exists(manifest_path):
        print("[WARN] themes/manifest.json not found, skipping theme CSS injection")
        return []

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    themes = manifest.get("themes", [])
    themes_sorted = sorted(themes, key=lambda t: t.get("order", 99))

    # Собираем CSS тем
    themes_css_parts = []
    for theme in themes_sorted:
        key = theme["key"]
        css_file = os.path.join(themes_dir, f"{key}.css")
        if os.path.exists(css_file):
            with open(css_file, encoding="utf-8") as f:
                themes_css_parts.append(f.read())
        else:
            print(f"[WARN] Theme CSS not found: {css_file}")

    # Читаем базовый style.css (без тем)
    base_css_path = os.path.join(engine_assets_dir, "style.css")
    base_css = ""
    if os.path.exists(base_css_path):
        with open(base_css_path, encoding="utf-8") as f:
            base_css = f.read()

    # Объединяем: сначала темы, затем базовые правила
    combined_css = "\n".join(themes_css_parts) + "\n" + base_css

    # Пишем в dist/assets/style.css
    os.makedirs(dist_assets_dir, exist_ok=True)
    out_path = os.path.join(dist_assets_dir, "style.css")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(combined_css)

    print(f"      Темы CSS собраны: {[t['key'] for t in themes_sorted]} → dist/assets/style.css")
    return themes

def copy_theme_assets(engine_assets_dir: str, dist_assets_dir: str, themes: list) -> None:
    """Ассеты тем (themes/<key>/: шрифты, текстуры) — для всех тем манифеста (themes — из build_themed_css)."""
    for theme in themes:
        # assets_from — папка ассетов другой темы (retro-manual берёт шрифты vintage); путь в dist тот же, что в CSS
        folder = theme.get("assets_from", theme["key"])
        src = os.path.join(engine_assets_dir, "themes", folder)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dist_assets_dir, "themes", folder), dirs_exist_ok=True)

def apply_book_assets(config: BookConfig, dist_assets_dir: str) -> None:
    """Ассеты книги поверх ассетов движка: overrides/assets/** заменяют файлы, extra.css и extra.js добавляются."""
    overrides = config.path(os.path.join(config.layout.overrides_dir, "assets"))
    if os.path.isdir(overrides):
        for root, _, files in os.walk(overrides):
            target = os.path.join(dist_assets_dir, os.path.relpath(root, overrides))
            os.makedirs(target, exist_ok=True)
            for f in files:
                shutil.copy2(os.path.join(root, f), os.path.join(target, f))
    for name in ("extra.css", "extra.js"):
        src = config.path(os.path.join(config.layout.extra_assets_dir, name))
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(dist_assets_dir, name))


def copy_media_assets(engine_assets_dir: str, dist_assets_dir: str) -> None:
    """media.css и media.js — только для книг с [media] enabled = true."""
    for name in MEDIA_ASSETS:
        shutil.copy2(os.path.join(engine_assets_dir, name), os.path.join(dist_assets_dir, name))


def write_credits_page(config: BookConfig, scanner: KnowledgeBaseScanner, converter: MarkdownConverter,
                       dist_dir: str, version: str) -> str:
    """Служебная страница «Иллюстрации и лицензии» ([media] credits_page): все изображения книги."""
    rel = config.media.credits_page
    if rel in scanner.articles_by_path:
        raise BuildError(f"media.credits_page: путь {rel} занят страницей {scanner.articles_by_path[rel].source_path}")
    body = credits_page_html(scanner.media, converter.media_usage, rel, config)
    page = Article(title=config.t("media.credits_title"), source_path="", rel_output_path=rel,
                   module_num=0, module_name="")
    page.size_bytes = len(body.encode("utf-8"))
    html_text = render_article_page(article=page, article_html=body, toc=[], modules_tree=scanner.modules_tree,
                                    total_articles=scanner.content_count, version=version, config=config,
                                    module_tag=config.t("media.credits_tag"))
    path = os.path.join(dist_dir, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(html_text)
    return path


def generate_nav_data_js(modules_tree, content_count: int, dist_dir: str) -> None:
    """Дерево навигации для гибридного сайдбара: assets/nav-data.js (подключается через <script defer>).

    Компактно: страница — [название, путь от корня сайта]; index — заглавная страница узла.
    """
    page = lambda a: [a.title, a.rel_output_path] if a else None
    data = {"count": content_count, "modules": [{
        "num": m["num"], "title": m["title"], "index": page(m.get("index")),
        "items": [page(a) for a in m["articles"]],
        "subs": [{"name": s["name"], "index": page(s.get("index")), "items": [page(a) for a in s["articles"]]}
                 for s in m["subsections"]],
    } for m in modules_tree]}
    path = os.path.join(dist_dir, "assets", "nav-data.js")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write("window.NAV_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")


def generate_search_data_js(articles: List[Article], dist_dir: str):
    """
    Генерация поискового индекса в виде search-data.js.
    Позволяет поиску работать локально через протокол file:/// без блокировок CORS.
    """
    search_items = []
    for art in articles:
        search_items.append({
            "title": art.title,
            "url": art.rel_output_path,
            "module": art.module_name,
            "sub": art.subsection_name,
            "num": art.module_num
        })

    js_content = f"window.SEARCH_DATA = {json.dumps(search_items, ensure_ascii=False, indent=2)};\n"
    assets_dir = os.path.join(dist_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    with open(os.path.join(assets_dir, "search-data.js"), "w", encoding="utf-8") as fp:
        fp.write(js_content)

def build(
    config: BookConfig,
    sources_dir: Optional[str] = None,
    dist_dir: str = "./dist",
    limit: Optional[int] = None,
    target_module: Optional[int] = None,
    is_pilot: bool = False,
    strict: bool = False
) -> List[str]:
    """Сборка книги. Возвращает предупреждения; strict=True — при предупреждениях BuildError."""
    # Ядро в книге не редактируется: предупреждаем о локальных правках engine/ (если есть .checksums.json)
    issues = verify_checksums()
    if issues:
        print(f"[WARN] engine/ изменён локально ({len(issues)}): " + "; ".join(issues[:5]))

    # 0. Чтение и валидация версии книги (book.toml: version или version_file + version_pattern)
    project_version = get_book_version(config)
    sources_dir = sources_dir or config.path(config.content.root)

    start_time = time.time()
    print("=====================================================================")
    print("🚀 Старт сборки книги (html-textbook-engine)")
    print(f"📌 Версия книги: v{project_version}")
    print("=====================================================================")

    # 1. Сканирование базы знаний
    print(f"\n[1/4] 🔍 Сканирование директории {sources_dir}...")
    scanner = KnowledgeBaseScanner(sources_dir, config)
    all_articles = scanner.scan()
    print(f"      Всего обнаружено статей: {len(all_articles)}")
    print(f"      Всего модулей: {len(scanner.modules_tree)}")
    media = library_for(scanner)        # [media]: папки media/ и credits.toml (ошибка в credits.toml — MediaError)
    if media is not None:
        print(f"      Изображений в папках {config.media.dir_name}/: {len(media.files)} "
              f"({media.total_bytes / 1048576:.1f} МБ)")
    module_nums = {m["num"] for m in scanner.modules_tree}
    for ov in config.overlays:
        missing = [n for n in ov["modules"] if n not in module_nums]
        if missing:
            raise BuildError(f"overlays «{ov['title']}»: нет модулей с номерами {missing}")

    # Фильтрация если указан --pilot, --limit или --module
    articles_to_build = all_articles
    if is_pilot:
        # Пилотный режим: первые 15 статей Модуля 1
        articles_to_build = [a for a in all_articles if a.module_num == 1][:15]
        print(f"      🔥 Режим ПИЛОТА: выбрано первых {len(articles_to_build)} статей Модуля 1")
    elif target_module is not None:
        articles_to_build = [a for a in all_articles if a.module_num == target_module]
        if limit:
            articles_to_build = articles_to_build[:limit]
        print(f"      🎯 Выбран модуль {target_module}: {len(articles_to_build)} статей")
    elif limit is not None:
        articles_to_build = all_articles[:limit]
        print(f"      ⚠️ Ограничение сборки: первые {limit} статей")

    # 2. Подготовка директорий и копирование ассетов
    print(f"\n[2/4] 📦 Подготовка директории {dist_dir} и копирование ассетов...")
    engine_assets = os.path.join(os.path.dirname(__file__), "assets")
    dist_assets = os.path.join(dist_dir, "assets")
    copy_assets(engine_assets, dist_assets)
    themes_list = build_themed_css(engine_assets, dist_assets)
    copy_theme_assets(engine_assets, dist_assets, themes_list)
    if media is not None:
        copy_media_assets(engine_assets, dist_assets)
    apply_book_assets(config, dist_assets)
    if media is not None:
        media.copy_to(dist_dir)
    generate_search_data_js(all_articles, dist_dir)
    if config.navigation.mode == "hybrid":
        generate_nav_data_js(scanner.modules_tree, scanner.content_count, dist_dir)
    
    # Копирование фавиконок книги в корень dist/ и в dist/assets/
    for fav in [config.branding.favicon_svg, config.branding.favicon_ico]:
        if fav:
            src_fav = config.path(fav)
            shutil.copy2(src_fav, os.path.join(dist_dir, os.path.basename(fav)))
            shutil.copy2(src_fav, os.path.join(dist_assets, os.path.basename(fav)))
    set_asset_versions(dist_dir, VERSIONED_ASSETS)
    print("      Ассеты, иконки favicon и файл search-data.js успешно развернуты.")

    # 3. Конвертация Markdown и генерация HTML страниц
    print(f"\n[3/4] ⚙️ Конвертация {len(articles_to_build)} статей в HTML...")
    converter = MarkdownConverter(scanner, config)
    built_count = 0
    total_mermaid_rendered = 0

    for i, art in enumerate(articles_to_build, 1):
        full_out_path = os.path.join(dist_dir, art.rel_output_path)
        os.makedirs(os.path.dirname(full_out_path), exist_ok=True)

        # Конвертация
        html_content, toc = converter.convert_article(art)
        
        # Рендеринг полного каркаса страницы
        page_html = render_article_page(
            article=art,
            article_html=html_content,
            toc=toc,
            modules_tree=scanner.modules_tree,
            total_articles=scanner.content_count,
            version=project_version,
            config=config,
            show_position=scanner.has_index_pages
        )

        with open(full_out_path, "w", encoding="utf-8") as fp:
            fp.write(page_html)

        built_count += 1
        total_mermaid_rendered += art.mermaid_count

        if i % 10 == 0 or i == len(articles_to_build):
            print(f"      Собрано: [{i:4d}/{len(articles_to_build)}] {art.title[:45]}...")

    if media is not None and config.media.credits_page:
        write_credits_page(config, scanner, converter, dist_dir, project_version)
        print(f"      Страница изображений и лицензий: {config.media.credits_page}")

    # 4. Генерация главной страницы (index.html)
    print("\n[4/4] 🏠 Генерация главной страницы (index.html)...")
    index_html = render_index_page(
        modules_tree=scanner.modules_tree,
        total_articles=scanner.content_count,
        total_mermaid=sum(a.mermaid_count for a in all_articles),
        version=project_version,
        config=config
    )
    index_path = os.path.join(dist_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as fp:
        fp.write(index_html)
    print("      index.html успешно создан.")

    warnings = converter.warnings
    if warnings:
        print(f"\n⚠️ Предупреждения сборки: {len(warnings)}")
        for w in warnings[:20]:
            print(f"   {w}")
        if len(warnings) > 20:
            print(f"   … и ещё {len(warnings) - 20}")
    if strict and warnings:
        raise BuildError(f"--strict: {len(warnings)} предупреждений")

    elapsed = time.time() - start_time
    print("\n=====================================================================")
    print(f"✅ СБОРКА УСПЕШНО ЗАВЕРШЕНА за {elapsed:.2f} сек!")
    print(f"   Сгенерировано страниц: {built_count}")
    print(f"   Отрендерено диаграмм Mermaid: {total_mermaid_rendered}")
    print(f"   Выходная директория: {os.path.abspath(dist_dir)}")
    print(f"   Главная страница: file://{os.path.abspath(index_path)}")
    print("=====================================================================")
    return warnings


class BuildError(RuntimeError):
    """Ошибка сборки (оверлеи, предупреждения в режиме --strict)."""


def main():
    parser = argparse.ArgumentParser(description="Сборка книги движком html-textbook-engine")
    parser.add_argument("--all", action="store_true", help="Собрать все статьи")
    parser.add_argument("--pilot", action="store_true", help="Собрать пилотную версию (первые 15 статей Модуля 1)")
    parser.add_argument("--module", type=int, help="Собрать конкретный номер модуля")
    parser.add_argument("--limit", type=int, help="Ограничить количество собираемых статей")
    parser.add_argument("--book", default=None, help="Путь к book.toml (по умолчанию ./book.toml)")
    parser.add_argument("--sources", default=None, help="Путь к исходникам (по умолчанию content.root из book.toml)")
    parser.add_argument("--dist", default="./dist", help="Выходная папка (по умолчанию ./dist)")
    parser.add_argument("--strict", action="store_true", help="Предупреждения (неизвестные выноски, неоднозначные ссылки, незакрытые ограды) — ошибки")

    args = parser.parse_args()

    # По умолчанию, если ничего не передано, собираем пилот
    is_pilot = args.pilot or (not args.all and args.module is None and args.limit is None)

    build(
        config=load_config(args.book),
        sources_dir=args.sources,
        dist_dir=args.dist,
        limit=args.limit,
        target_module=args.module,
        is_pilot=is_pilot,
        strict=args.strict
    )

if __name__ == "__main__":
    main()
