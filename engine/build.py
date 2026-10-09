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
from .converter import MarkdownConverter
from .config import BookConfig, load_config
from .template import render_article_page, render_index_page, get_book_version

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
            # style.css обрабатывается build_themed_css
            if f == "style.css":
                continue
            src_f = os.path.join(root, f)
            dst_f = os.path.join(target_dir, f)
            shutil.copy2(src_f, dst_f)

def build_themed_css(engine_assets_dir: str, dist_assets_dir: str) -> list:
    """
    Читает manifest.json из themes/, конкатенирует CSS файлы тем
    с основным style.css и записывает итоговый style.css в dist/assets/.
    Возвращает список словарей тем из манифеста.
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
    is_pilot: bool = False
):
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
    generate_search_data_js(all_articles, dist_dir)
    
    # Копирование фавиконок книги в корень dist/ и в dist/assets/
    for fav in [config.branding.favicon_svg, config.branding.favicon_ico]:
        if fav:
            src_fav = config.path(fav)
            shutil.copy2(src_fav, os.path.join(dist_dir, os.path.basename(fav)))
            shutil.copy2(src_fav, os.path.join(dist_assets, os.path.basename(fav)))
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

    elapsed = time.time() - start_time
    print("\n=====================================================================")
    print(f"✅ СБОРКА УСПЕШНО ЗАВЕРШЕНА за {elapsed:.2f} сек!")
    print(f"   Сгенерировано страниц: {built_count}")
    print(f"   Отрендерено диаграмм Mermaid: {total_mermaid_rendered}")
    print(f"   Выходная директория: {os.path.abspath(dist_dir)}")
    print(f"   Главная страница: file://{os.path.abspath(index_path)}")
    print("=====================================================================")

def main():
    parser = argparse.ArgumentParser(description="Сборка книги движком html-textbook-engine")
    parser.add_argument("--all", action="store_true", help="Собрать все статьи")
    parser.add_argument("--pilot", action="store_true", help="Собрать пилотную версию (первые 15 статей Модуля 1)")
    parser.add_argument("--module", type=int, help="Собрать конкретный номер модуля")
    parser.add_argument("--limit", type=int, help="Ограничить количество собираемых статей")
    parser.add_argument("--book", default=None, help="Путь к book.toml (по умолчанию ./book.toml)")
    parser.add_argument("--sources", default=None, help="Путь к исходникам (по умолчанию content.root из book.toml)")
    parser.add_argument("--dist", default="./dist", help="Выходная папка (по умолчанию ./dist)")

    args = parser.parse_args()

    # По умолчанию, если ничего не передано, собираем пилот
    is_pilot = args.pilot or (not args.all and args.module is None and args.limit is None)

    build(
        config=load_config(args.book),
        sources_dir=args.sources,
        dist_dir=args.dist,
        limit=args.limit,
        target_module=args.module,
        is_pilot=is_pilot
    )

if __name__ == "__main__":
    main()
