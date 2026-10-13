"""Темы оформления: манифест, доступность тем книге, ассеты, контраст тем."""
import os
import re
import tempfile
import unittest

from engine import themes
from engine.build import build_themed_css, copy_theme_assets
from engine.config import ConfigError, load_config
from engine.template import book_runtime_data, make_html_tag, theme_switcher_html

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def load(text=""):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "book.toml")
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)
        return load_config(path)


def luminance(hex_color):
    h = hex_color.lstrip("#")
    channels = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a, b):
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


ALL_THEMES = ("light", "paper", "slate", "mirage", "night", "groove", "amber", "vintage", "retro-manual", "modern-manual", "synthwave", "cyberpunk", "retro-green", "retro-amber", "retro-gaming")
# Базовые темы paper, light и amber проверены вручную (рефы), здесь — остальные
DESIGNED = ("slate", "mirage", "night", "groove", "vintage", "modern-manual", "retro-manual", "synthwave", "cyberpunk", "retro-green", "retro-amber", "retro-gaming")
LIGHT_THEMES = ("vintage", "modern-manual", "retro-manual")  # остальные — тёмные


def theme_vars(key):
    with open(os.path.join(ASSETS_DIR, "themes", f"{key}.css"), encoding="utf-8") as fp:
        css = fp.read()
    # Vintage: палитра бумаги — в блоке листа (.article-body и .index-container), блок самой темы — Amber для хрома
    sheet = r'\[data-theme="' + key + r'"\] \.article-body,\s*\[data-theme="' + key + r'"\] \.index-container\s*\{(.*?)\n\}'
    m = re.search(sheet, css, re.S) or re.search(r'\[data-theme="' + key + r'"\]\s*\{(.*?)\n\}', css, re.S)
    block = m.group(1)
    return {name: value.strip() for name, value in re.findall(r"--([a-z0-9-]+):\s*([^;]+);", block)
            if re.fullmatch(r"#[0-9a-fA-F]{6}", value.strip())}


class ManifestTest(unittest.TestCase):
    def test_default_theme_and_order(self):
        default, active = themes.active_themes()
        self.assertEqual(default, "amber")
        self.assertEqual([t["key"] for t in active], list(ALL_THEMES))

    def test_no_experimental_flag_left(self):
        _, all_themes = themes.read_manifest()
        self.assertFalse([t["key"] for t in all_themes if "experimental" in t])


class ThemeAssetsTest(unittest.TestCase):
    def test_all_theme_assets_copied(self):
        with tempfile.TemporaryDirectory() as out:
            copy_theme_assets(ASSETS_DIR, out, build_themed_css(ASSETS_DIR, out))
            self.assertTrue(os.path.isfile(os.path.join(out, "themes", "vintage", "fonts", "Bitter-Variable.woff2")))
            self.assertTrue(os.path.isfile(os.path.join(out, "themes", "modern-manual", "fonts", "Jost-Variable.woff2")))

    def test_font_face_files_exist_and_are_woff2(self):
        for key in ("vintage", "retro-manual", "modern-manual"):
            with open(os.path.join(ASSETS_DIR, "themes", f"{key}.css"), encoding="utf-8") as fp:
                urls = re.findall(r'@font-face[^}]*?url\("([^"]+)"\)', fp.read())
            self.assertTrue(urls, key)
            for url in urls:
                self.assertTrue(os.path.isfile(os.path.join(ASSETS_DIR, url)), f"{key}: нет файла {url}")
                self.assertTrue(url.endswith(".woff2"), f"{key}: шрифт не сжат в woff2: {url}")

    def test_assets_from_reuses_other_folder(self):
        with tempfile.TemporaryDirectory() as out:
            copy_theme_assets(ASSETS_DIR, out, build_themed_css(ASSETS_DIR, out))
            self.assertTrue(os.path.isfile(os.path.join(out, "themes", "vintage", "fonts", "CourierPrime-Regular.woff2")))
            self.assertFalse(os.path.exists(os.path.join(out, "themes", "retro-manual")))


class ThemeOutputTest(unittest.TestCase):
    def test_css_contains_every_theme(self):
        with tempfile.TemporaryDirectory() as out:
            build_themed_css(ASSETS_DIR, out)
            with open(os.path.join(out, "style.css"), encoding="utf-8") as fp:
                css = fp.read()
        for key in ALL_THEMES:
            self.assertIn(f'[data-theme="{key}"]', css)

    def test_html_tag_and_runtime_list_all_themes(self):
        keys = ",".join(ALL_THEMES)
        self.assertIn(f'data-available-themes="{keys}"', make_html_tag())
        cfg = load("")
        self.assertEqual(book_runtime_data(cfg)["availableThemes"], list(ALL_THEMES))
        self.assertEqual(book_runtime_data(cfg)["themeNames"]["mirage"], "Mirage")

    def test_switcher_has_icon_for_every_theme(self):
        html = theme_switcher_html(load(""))
        for key in ALL_THEMES:
            self.assertIn(f'theme-icon-{key}', html)


class ConfigKeyTest(unittest.TestCase):
    def test_theme_section_removed(self):
        # Секция [theme] больше не существует: книга с ней получает ошибку, как и на любой неизвестный ключ
        with self.assertRaisesRegex(ConfigError, "неизвестные ключи"):
            load('[theme]\nexperimental = ["slate"]\n')


class DesignTest(unittest.TestCase):
    """Пороги WCAG: основной текст на фоне и в коде ≥ 7:1 (AAA), остальной текст ≥ 4.5:1 (AA).
    Ступени поверхностей растут по светлоте. Тёмный фон: светлота ниже 0.03 (Ayu Mirage — 0.022)."""

    def assertContrast(self, v, fg, bg, minimum):
        ratio = contrast(v[fg], v[bg])
        self.assertGreaterEqual(ratio, minimum, f"{fg} на {bg}: {ratio:.2f} < {minimum}")

    def test_body_text_meets_aaa(self):
        for key in DESIGNED:
            v = theme_vars(key)
            for bg in ("bg", "code-bg"):
                with self.subTest(theme=key, bg=bg):
                    self.assertContrast(v, "text", bg, 7.0)
            # bg-elevated в движке не используется: здесь достаточно AA для основного текста
            with self.subTest(theme=key, bg="bg-elevated"):
                self.assertContrast(v, "text", "bg-elevated", 4.5)

    def test_secondary_text_meets_aa(self):
        for key in DESIGNED:
            v = theme_vars(key)
            for fg in ("text-secondary", "text-muted", "text-subtle", "accent", "link"):
                for bg in ("bg", "bg-surface", "bg-card", "bg-card-hover"):
                    with self.subTest(theme=key, fg=fg, bg=bg):
                        self.assertContrast(v, fg, bg, 4.5)
            with self.subTest(theme=key, fg="code-comment"):
                self.assertContrast(v, "code-comment", "code-bg", 4.5)
            with self.subTest(theme=key, fg="code-punctuation"):
                self.assertContrast(v, "code-punctuation", "code-bg", 4.5)

    def test_status_colours_meet_aa(self):
        for key in DESIGNED:
            v = theme_vars(key)
            for fg in ("success", "warning", "danger"):
                with self.subTest(theme=key, fg=fg):
                    self.assertContrast(v, fg, "bg-card", 4.5)

    def test_mermaid_labels_meet_aa(self):
        for key in DESIGNED:
            v = theme_vars(key)
            for name in ("process", "success", "error", "warning", "entry", "aux", "system", "data", "network", "accent"):
                with self.subTest(theme=key, node=name):
                    self.assertContrast(v, f"mm-{name}-text", f"mm-{name}-fill", 4.5)

    def test_surfaces_step_up_in_lightness(self):
        order = ["bg", "bg-surface", "bg-card", "bg-card-hover", "bg-elevated"]
        for key in DESIGNED:
            v = theme_vars(key)
            lums = [luminance(v[name]) for name in order]
            with self.subTest(theme=key):
                self.assertEqual(lums, sorted(lums))
                self.assertEqual(len(set(lums)), len(lums))

    def test_background_matches_mode(self):
        for key in DESIGNED:
            v = theme_vars(key)
            with self.subTest(theme=key):
                if key in LIGHT_THEMES:
                    self.assertGreater(luminance(v["bg"]), 0.35)  # бумага: светлая, но не белая
                    self.assertLess(luminance(v["text"]), 0.05)   # чернила
                else:
                    self.assertLess(luminance(v["bg"]), 0.03)     # тёмный фон: светлота ниже 0.03
                    self.assertNotEqual(v["bg"], "#000000")


if __name__ == "__main__":
    unittest.main()
