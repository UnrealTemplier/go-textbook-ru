"""Инлайн-код и шрифт кода: вшитый Engine Mono (Cascadia Code, OFL) и цвет, выведенный из темы.

Статические проверки — файлы и @font-face. Браузерная проверка (headless Firefox) обходит все темы на странице
демо-книги и меряет итоговый цвет кода: контраст к плашке не ниже порога, не выше контраста основного текста
(код не ярче текста), оттенок близок к акценту темы. Без Firefox браузерная часть пропускается.
"""
import contextlib
import io
import math
import os
import re
import tempfile
import unittest

from engine.build import build
from engine.config import load_config
from engine.tests import DEMO_ROOT, HAS_DEMO
from engine.tests.firefox import BROWSER, probe
from engine.tests.test_themes import ALL_THEMES

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
PAGE = "docs/01-osnovy/1-spiski-i-kod.html"
MIN_CONTRAST = 6.0  # у акцентов тем контраст к плашке от 5.0; код не должен быть бледнее
MAX_HUE_SHIFT = 40  # градусов в OKLab относительно акцента темы (у приглушённых акцентов, как в Groove, оттенок смещается заметнее)

SCRIPT = """(function(){
var st=document.createElement('style');st.textContent='*{transition:none!important}';document.head.appendChild(st);
var code=document.querySelector('.article-markdown :not(pre) > code');
var cx=document.createElement('canvas').getContext('2d',{willReadFrequently:true});
function rgb(v){cx.clearRect(0,0,1,1);cx.fillStyle='#000';cx.fillStyle=v;cx.fillRect(0,0,1,1);var d=cx.getImageData(0,0,1,1).data;return 'rgb('+d[0]+', '+d[1]+', '+d[2]+')';}
function snap(key){document.documentElement.setAttribute('data-theme',key);var c=getComputedStyle(code);
return {key:key,color:rgb(c.color),raw:c.color,bg:rgb(c.backgroundColor),border:c.borderTopColor,text:rgb(c.getPropertyValue('--text').trim()),
link:c.getPropertyValue('--link').trim(),weight:c.fontWeight,family:c.fontFamily};}
function go(){
var keys=%s,out=[];
document.fonts.load('500 14px "Engine Mono"').then(function(f){
keys.forEach(function(k){out.push(snap(k));});
send({themes:out,font:document.fonts.check('500 14px "Engine Mono"'),loaded:f.length});});}
setTimeout(go,800);})();"""


def parse_color(value):
    """rgb()/rgba()/color(srgb ...) → (r, g, b) в долях единицы."""
    m = re.match(r"rgba?\(([^)]*)\)", value)
    if m:
        parts = [p for p in re.split(r"[ ,/]+", m.group(1).strip()) if p]
        return tuple(float(p) / 255 for p in parts[:3])
    m = re.match(r"color\(srgb ([^)]*)\)", value)
    if m:
        parts = [p for p in re.split(r"[ /]+", m.group(1).strip()) if p]
        return tuple(float(p) for p in parts[:3])
    h = value.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def oklab_hue(rgb):
    r, g, b = (to_linear(c) for c in rgb)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return math.degrees(math.atan2(bb, a)), math.hypot(a, bb)


class FontFilesTest(unittest.TestCase):
    def test_font_and_license_shipped(self):
        fonts = os.path.join(ASSETS_DIR, "fonts")
        font = os.path.join(fonts, "EngineMono-Variable.woff2")
        self.assertTrue(os.path.isfile(font))
        with open(font, "rb") as fp:
            self.assertEqual(fp.read(4), b"wOF2")
        self.assertLess(os.path.getsize(font), 200_000, "шрифт кода раздулся: обрежьте до латиницы и кириллицы")
        self.assertTrue(os.path.isfile(os.path.join(fonts, "OFL-cascadiacode.txt")))

    def test_font_face_and_stack(self):
        with open(os.path.join(ASSETS_DIR, "style.css"), encoding="utf-8") as fp:
            css = fp.read()
        self.assertIn('url("fonts/EngineMono-Variable.woff2")', css)
        self.assertRegex(css, r'--font-mono:\s*"Engine Mono"')
        self.assertNotRegex(css, r"JetBrains Mono|Roboto Mono|Ubuntu Mono|Noto Sans Mono")

    def test_themes_do_not_hardcode_inline_code_colors(self):
        for key in ALL_THEMES:
            with open(os.path.join(ASSETS_DIR, "themes", f"{key}.css"), encoding="utf-8") as fp:
                self.assertNotIn("--code-inline", fp.read(), f"{key}: цвет инлайн-кода задан вручную")

    def test_inline_code_font_is_built_into_dist(self):
        with tempfile.TemporaryDirectory() as tmp:
            from engine.build import copy_assets
            copy_assets(ASSETS_DIR, os.path.join(tmp, "assets"))
            self.assertTrue(os.path.isfile(os.path.join(tmp, "assets", "fonts", "EngineMono-Variable.woff2")))


@unittest.skipUnless(HAS_DEMO, "демо-книги нет: это книга, а не репозиторий движка")
@unittest.skipUnless(BROWSER, "нет Firefox (PATH или MERMAID_BROWSER)")
class InlineCodeColorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        dist = os.path.join(cls.tmp.name, "dist")
        with contextlib.redirect_stdout(io.StringIO()):
            build(load_config(os.path.join(DEMO_ROOT, "book.toml")), dist_dir=dist, is_pilot=False)
        keys = "[" + ",".join('"%s"' % k for k in ALL_THEMES) + "]"
        cls.result = probe(os.path.join(dist, PAGE), lambda html: html, SCRIPT % keys)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_font_loaded(self):
        self.assertIsNotNone(self.result, "страница не отправила результат в Firefox")
        self.assertTrue(self.result["font"], "Engine Mono не загрузился по file://")

    def test_every_theme(self):
        self.assertIsNotNone(self.result)
        self.assertEqual([t["key"] for t in self.result["themes"]], list(ALL_THEMES))
        for t in self.result["themes"]:
            key = t["key"]
            code, plate, text = parse_color(t["color"]), parse_color(t["bg"]), parse_color(t["text"])
            ratio, text_ratio = contrast(code, plate), contrast(text, plate)
            self.assertGreaterEqual(ratio, MIN_CONTRAST, f"{key}: код бледен ({ratio:.1f})")
            link = parse_color(t["link"])
            # Код не ярче основного текста темы (--text) и не ярче акцента, если акцент сам ярче текста (Mirage)
            limit = max(text_ratio, contrast(link, plate))
            self.assertLessEqual(ratio, limit + 0.05, f"{key}: код ярче текста и акцента ({ratio:.1f} > {limit:.1f})")
            hue_code, chroma = oklab_hue(code)
            hue_link, _ = oklab_hue(link)
            shift = abs((hue_code - hue_link + 180) % 360 - 180)
            if chroma > 0.02:  # у почти серого цвета оттенок не определён
                self.assertLessEqual(shift, MAX_HUE_SHIFT, f"{key}: оттенок кода ушёл от акцента на {shift:.0f}°")

    def test_weight_is_variable_driven(self):
        self.assertIsNotNone(self.result)
        for t in self.result["themes"]:
            expected = "400" if t["key"] in ("vintage", "retro-manual") else "500"
            self.assertEqual(t["weight"], expected, t["key"])
