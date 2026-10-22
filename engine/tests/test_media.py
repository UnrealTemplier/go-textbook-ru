"""Изображения уроков ([media], engine/media.py): размеры из заголовков, credits.toml и лицензии,
конфиг, сканер, конвертер (figure, галерея, встраивание), копирование в dist/. Аудит — test_audit_media.py.

Эталонные файлы собираются в памяти (несколько десятков байт): PNG, GIF, JPEG (с Exif-поворотом),
WebP (VP8, VP8L, VP8X), SVG, AVIF. Без браузера; рантайм окна увеличения — test_media_runtime.py.
"""
import contextlib
import io
import os
import struct
import tempfile
import unittest
import zlib

from engine.audit import SiteAuditor
from engine.build import BuildError, build
from engine.config import BookConfig, ConfigError, load_config
from engine.converter import MarkdownConverter
from engine.media import MediaError, image_size, license_allowed, load_credits, normalize_license
from engine.scanner import KnowledgeBaseScanner, ScanError, slugify


# ---------------------------------------------------------------------------
# Эталонные изображения
# ---------------------------------------------------------------------------
def png_bytes(w, h):
    raw = b"".join(b"\x00" + b"\x80\x80\x80" * w for _ in range(h))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def gif_bytes(w, h):
    return b"GIF89a" + struct.pack("<HH", w, h) + b"\x00\x00\x00" + b"\x3b"


def jpeg_bytes(w, h, orientation=None):
    out = b"\xff\xd8\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    if orientation:
        tiff = (b"MM\x00\x2a" + struct.pack(">I", 8) + struct.pack(">H", 1)
                + struct.pack(">HHIHH", 0x0112, 3, 1, orientation, 0) + struct.pack(">I", 0))
        seg = b"Exif\x00\x00" + tiff
        out += b"\xff\xe1" + struct.pack(">H", len(seg) + 2) + seg
    out += b"\xff\xc4" + struct.pack(">H", 5) + b"\x00\x00\x00"           # DHT (C4) — не SOF
    out += b"\xff\xc0" + struct.pack(">HBHHB", 17, 8, h, w, 3) + b"\x01\x22\x00\x02\x11\x01\x03\x11\x01"
    return out + b"\xff\xd9"


def webp_bytes(kind, w, h):
    if kind == "VP8 ":
        payload = b"\x00\x00\x00" + b"\x9d\x01\x2a" + struct.pack("<HH", w, h) + b"\x00" * 4
    elif kind == "VP8L":
        payload = b"\x2f" + struct.pack("<I", (w - 1) | ((h - 1) << 14)) + b"\x00" * 4
    else:
        payload = b"\x00\x00\x00\x00" + (w - 1).to_bytes(3, "little") + (h - 1).to_bytes(3, "little")
    chunk = kind.encode() + struct.pack("<I", len(payload)) + payload
    return b"RIFF" + struct.pack("<I", 4 + len(chunk)) + b"WEBP" + chunk


def box(kind, payload):
    return struct.pack(">I", 8 + len(payload)) + kind + payload


def avif_bytes(w, h, tile=None):
    ispe = lambda a, b: box(b"ispe", b"\x00\x00\x00\x00" + struct.pack(">II", a, b))
    props = (ispe(*tile) if tile else b"") + ispe(w, h)
    meta = box(b"meta", b"\x00\x00\x00\x00" + box(b"hdlr", b"\x00" * 24) + box(b"iprp", box(b"ipco", props)))
    return box(b"ftyp", b"avif\x00\x00\x00\x00mif1avif") + meta + box(b"mdat", b"")


def write(root, rel, data):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fp:
        fp.write(data if isinstance(data, bytes) else data.encode("utf-8"))
    return path


class ImageSizeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def size(self, name, data):
        return image_size(write(self.tmp.name, name, data))

    def test_raster_formats(self):
        self.assertEqual(self.size("a.png", png_bytes(7, 3)), (7, 3))
        self.assertEqual(self.size("a.gif", gif_bytes(640, 480)), (640, 480))
        self.assertEqual(self.size("a.jpg", jpeg_bytes(1600, 1067)), (1600, 1067))
        self.assertEqual(self.size("a.jpeg", jpeg_bytes(30, 20)), (30, 20))

    def test_jpeg_exif_rotation_swaps_sides(self):
        self.assertEqual(self.size("r.jpg", jpeg_bytes(4000, 3000, orientation=6)), (3000, 4000))
        self.assertEqual(self.size("n.jpg", jpeg_bytes(4000, 3000, orientation=1)), (4000, 3000))

    def test_webp_variants(self):
        self.assertEqual(self.size("lossy.webp", webp_bytes("VP8 ", 1600, 900)), (1600, 900))
        self.assertEqual(self.size("lossless.webp", webp_bytes("VP8L", 1000, 16383)), (1000, 16383))
        self.assertEqual(self.size("ext.webp", webp_bytes("VP8X", 20000, 3)), (20000, 3))

    def test_svg(self):
        self.assertEqual(self.size("a.svg", '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="40px"/>'), (120, 40))
        self.assertEqual(self.size("b.svg", '<?xml version="1.0"?><!-- <svg width="1"> -->\n'
                                            '<svg viewBox="0 0 300.5 150" xmlns="http://www.w3.org/2000/svg"></svg>'), (300, 150))
        self.assertEqual(self.size("c.svg", '<svg width="600" viewBox="0,0,300,100"></svg>'), (600, 200))
        self.assertEqual(self.size("d.svg", '<svg width="100%" height="100%" viewBox="0 0 64 32"></svg>'), (64, 32))
        self.assertIsNone(self.size("e.svg", '<svg width="10em"></svg>'))

    def test_avif(self):
        self.assertEqual(self.size("a.avif", avif_bytes(1920, 1080)), (1920, 1080))
        self.assertEqual(self.size("grid.avif", avif_bytes(2048, 1024, tile=(512, 512))), (2048, 1024))
        self.assertIsNone(self.size("heic.avif", box(b"ftyp", b"heic\x00\x00\x00\x00mif1") + box(b"mdat", b"")))

    def test_garbage_and_wrong_extension(self):
        self.assertIsNone(self.size("x.png", b"not an image at all"))
        self.assertIsNone(self.size("empty.webp", b""))
        self.assertEqual(self.size("really-png.jpg", png_bytes(5, 6)), (5, 6))   # сигнатура важнее расширения
        self.assertIsNone(image_size(os.path.join(self.tmp.name, "missing.png")))


class LicensesAndCreditsTest(unittest.TestCase):
    ALLOWED = ["PD", "CC0", "CC BY", "CC BY-SA", "own"]

    def test_license_matching(self):
        self.assertEqual(normalize_license(" cc-by-sa_4.0 "), "CC BY SA 4.0")
        for ok in ("PD", "pd", "CC0", "CC0 1.0", "CC BY", "CC BY 4.0", "CC-BY-SA 3.0", "CC BY-SA 3.0 DE", "own", "OWN"):
            self.assertTrue(license_allowed(ok, self.ALLOWED), ok)
        for bad in ("CC BY-NC 4.0", "CC BY-ND 2.0", "CC BY-NC-SA 4.0", "GFDL", "PD-old", "", "все права защищены"):
            self.assertFalse(license_allowed(bad, self.ALLOWED), bad)
        self.assertTrue(license_allowed("GFDL 1.2", ["GFDL"]))

    def test_load_credits(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = write(tmp, "ok.toml", '["a.webp"]\ncaption = "Подпись"\nlicense = "PD"\ninvert_dark = true\n')
            self.assertEqual(load_credits(good)["a.webp"]["caption"], "Подпись")
            for text, err in (('["a.webp"]\nlicence = "PD"\n', "неизвестные ключи"),
                              ('["a.webp"]\ninvert_dark = "yes"\n', "true или false"),
                              ('["a.webp"]\nauthor = 5\n', "строка"),
                              ('caption = "без таблицы"\n', "ожидается таблица"),
                              ('["a.webp"\n', "")):
                with self.assertRaisesRegex(MediaError, err):
                    load_credits(write(tmp, "bad.toml", text))


class MediaConfigTest(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            return load_config(write(tmp, "book.toml", text))

    def test_defaults_off(self):
        m = BookConfig().media
        self.assertFalse(m.enabled)
        self.assertEqual((m.dir_name, m.credits_file, m.credits_page), ("media", "credits.toml", ""))
        self.assertEqual(m.extensions, ["webp", "png", "jpg", "jpeg", "gif", "svg", "avif"])
        self.assertEqual((m.figures, m.lightbox, m.require_alt, m.require_credit), (True, True, True, True))
        self.assertEqual((m.max_file_kb, m.max_dimension_px, m.budget_mb), (500, 2000, 700))
        self.assertEqual(m.allowed_licenses, ["PD", "CC0", "CC BY", "CC BY-SA", "own"])

    def test_values_and_normalization(self):
        cfg = self.load('[media]\nenabled = true\nextensions = [".PNG", "webp"]\ncredits_page = "docs/credits.html"\n')
        self.assertTrue(cfg.media.enabled)
        self.assertEqual(cfg.media.extensions, ["png", "webp"])

    def test_errors(self):
        for text, err in (('[media]\nenabld = true\n', "неизвестные ключи"),
                          ('[media]\ndir_name = "a/b"\n', "dir_name"),
                          ('[media]\ncredits_file = ""\n', "credits_file"),
                          ('[media]\nextensions = "png"\n', "extensions"),
                          ('[media]\nmax_file_kb = -1\n', "max_file_kb"),
                          ('[media]\nbudget_mb = true\n', "budget_mb"),
                          ('[media]\ncredits_page = "../x.html"\n', "credits_page"),
                          ('[media]\ncredits_page = "credits"\n', "credits_page"),
                          ('[media]\ncredits_page = "index.html"\n', "credits_page")):
            with self.assertRaisesRegex(ConfigError, err, msg=text):
                self.load(text)


# ---------------------------------------------------------------------------
# Пробная книга
# ---------------------------------------------------------------------------
CREDITS_A = '''["a.png"]
caption = "Подпись из credits"
author = "Автор А"
license = "CC BY-SA 4.0"
license_url = "https://creativecommons.org/licenses/by-sa/4.0/"
source = "https://commons.wikimedia.org/wiki/File:A.png"
modified = "уменьшено"

["scheme.svg"]
alt = "Схема из credits"
license = "own"
invert_dark = true

["pd.gif"]
author = "U.S. Army"
license = "PD"
source = "https://example.org/pd"
'''


class MediaBook:
    """Временная книга: модуль с уроком и media/, вложенный раздел со своей media/."""

    def __init__(self, lesson, deep="# Глубокий урок\n\nТекст.\n", extra_toml="", files=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        src = "sources/1. Модуль"
        write(self.root, f"{src}/1. Урок.md", lesson)
        write(self.root, f"{src}/2. Раздел/1. Глубокий урок.md", deep)
        write(self.root, f"{src}/media/a.png", png_bytes(40, 20))
        write(self.root, f"{src}/media/scheme.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 90 30"/>')
        write(self.root, f"{src}/media/pd.gif", gif_bytes(8, 8))
        write(self.root, f"{src}/media/credits.toml", CREDITS_A)
        write(self.root, f"{src}/2. Раздел/media/b.png", png_bytes(10, 10))
        write(self.root, f"{src}/2. Раздел/media/credits.toml",
              '["b.png"]\nauthor = "Б"\nlicense = "CC0"\nsource = "https://example.org/b"\n')
        for rel, data in (files or {}).items():
            write(self.root, rel, data)
        write(self.root, "book.toml", '[project]\nversion = "1.0.0"\n[content]\ntitle_source = "h1"\n'
              '[media]\nenabled = true\n' + extra_toml)
        self.cfg = load_config(os.path.join(self.root, "book.toml"))
        self.dist = os.path.join(self.root, "dist")

    def convert(self, rel="1. Урок.md"):
        scanner = KnowledgeBaseScanner(self.cfg.path(self.cfg.content.root), self.cfg)
        scanner.scan()
        conv = MarkdownConverter(scanner, self.cfg)
        art = next(a for a in scanner.articles if a.source_path.endswith(rel))
        html, _ = conv.convert_article(art)
        return html, conv.warnings

    def build(self, strict=False):
        with contextlib.redirect_stdout(io.StringIO()):
            return build(self.cfg, dist_dir=self.dist, is_pilot=False, strict=strict)

    def audit(self, strict=False):
        a = SiteAuditor(self.dist, self.root, mermaid_runtime=False, config=self.cfg, strict=strict)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ok = a.run_audit()
        return ok, a, out.getvalue()

    def close(self):
        self.tmp.cleanup()


class ScannerMediaTest(unittest.TestCase):
    def test_media_dir_is_not_a_section(self):
        book = MediaBook("# Урок\n")
        try:
            scanner = KnowledgeBaseScanner(book.cfg.path("sources"), book.cfg)
            scanner.scan()
            mod = scanner.modules_tree[0]
            self.assertEqual([d["dir_name"] for d in mod["dirs"]], ["2. Раздел"])
            self.assertEqual([s["name"] for s in mod["subsections"]], ["2. Раздел"])
            dirs = {os.path.relpath(p, scanner.sources_dir): out for p, out in scanner.media_dirs}
            self.assertEqual(dirs, {".": "docs", "1. Модуль": "docs/01-modul",
                                    os.path.join("1. Модуль", "2. Раздел"): "docs/01-modul/2-razdel"})
        finally:
            book.close()

    def test_media_beside_pages_needs_no_pages_beside_subdirs(self):
        """media/ рядом со страницами раздела — не подкаталог: ошибки «статьи рядом с подкаталогами» нет,
        и раздел без настоящих подкаталогов сохраняет длину slug раздела."""
        name = "Очень длинное название раздела без подкаталогов"
        book = MediaBook("# Урок\n", files={f"sources/2. Второй/{name}/1. Стр.md": "# С\n",
                                            f"sources/2. Второй/{name}/media/x.png": png_bytes(1, 1)})
        try:
            scanner = KnowledgeBaseScanner(book.cfg.path("sources"), book.cfg)
            arts = scanner.scan()
            deep = next(a for a in arts if a.source_path.endswith("1. Стр.md"))
            self.assertEqual(deep.rel_output_path, f"docs/02-vtoroy/{slugify(name, book.cfg.slug.section)}/1-str.html")
            book.cfg.media.enabled = False                 # без [media] папка — обычный подкаталог
            plain = KnowledgeBaseScanner(book.cfg.path("sources"), book.cfg)
            with self.assertRaisesRegex(ScanError, "статьи рядом с подкаталогами"):
                plain.scan()
            self.assertEqual(plain.media_dirs, [])
        finally:
            book.close()


class ConverterMediaTest(unittest.TestCase):
    def convert(self, lesson, **kw):
        book = MediaBook(lesson, **kw)
        try:
            return book.convert()
        finally:
            book.close()

    def test_figure_with_caption_and_credit(self):
        html, warnings = self.convert('# Урок\n\n![Альт](media/a.png "Подпись из текста")\n')
        self.assertEqual(warnings, [])
        self.assertIn('<img class="md-media md-zoom" src="media/a.png" alt="Альт" width="40" height="20" '
                      'loading="lazy" decoding="async">', html)
        self.assertIn('<figcaption>Подпись из текста <span class="md-credit">Автор: Автор А · '
                      '<a href="https://creativecommons.org/licenses/by-sa/4.0/" rel="license">CC BY-SA 4.0</a> · '
                      '<a href="https://commons.wikimedia.org/wiki/File:A.png">источник</a> · изменения: уменьшено</span>'
                      '</figcaption>', html)
        self.assertNotIn("<p><img", html)

    def test_caption_and_alt_from_credits(self):
        html, _ = self.convert("# Урок\n\n![](media/a.png)\n\n![](media/scheme.svg)\n\n![](media/pd.gif)\n")
        self.assertIn('alt="Подпись из credits"', html)            # alt ← caption
        self.assertIn("<figcaption>Подпись из credits <span", html)
        self.assertIn('class="md-media md-zoom md-invert-dark" src="media/scheme.svg" alt="Схема из credits" '
                      'width="90" height="30"', html)
        self.assertNotIn("<figcaption></figcaption>", html)        # own без автора и подписи — без figcaption
        self.assertIn('<span class="md-credit">Автор: U.S. Army · общественное достояние · '
                      '<a href="https://example.org/pd">источник</a></span>', html)

    def test_gallery_and_inline(self):
        html, _ = self.convert("# Урок\n\n![a](media/a.png)\n![b](media/pd.gif) ![c](media/scheme.svg)\n\n"
                               "Текст ![значок](media/scheme.svg) в абзаце.\n")
        self.assertEqual(html.count('<div class="md-gallery">'), 1)
        gallery = html.split('<div class="md-gallery">', 1)[1].split("</div>", 1)[0]
        self.assertEqual(gallery.count('<figure class="md-figure">'), 3)
        self.assertIn('<p>Текст <img class="md-media md-zoom md-invert-dark" src="media/scheme.svg" alt="значок" '
                      'width="90" height="30" loading="lazy" decoding="async"> в абзаце.</p>', html)

    def test_embeds(self):
        html, warnings = self.convert("# Урок\n\n![[a.png|Встроенная подпись]]\n\nВ тексте ![[b.png]] из раздела.\n\n"
                                      "`![[a.png]]` в коде и ![[Урок]] — не картинка.\n")
        self.assertIn('src="media/a.png" alt="Встроенная подпись"', html)
        self.assertIn("<figcaption>Встроенная подпись <span", html)
        self.assertIn('src="2-razdel/media/b.png" alt=""', html)    # другой каталог: путь к копии в dist/
        self.assertIn("<code>![[a.png]]</code>", html)
        self.assertIn('!<a href="1-urok.html" class="wikilink">', html)   # ![[статья]] — по-прежнему wikilink
        self.assertEqual(warnings, [])

    def test_embed_from_deep_page_and_ambiguity(self):
        deep = "# Глубокий\n\n![[a.png]]\n\n![[b.png]]\n\n![[dup.png]]\n\n![[nope.png|Нет]]\n"
        book = MediaBook("# Урок\n", deep=deep, files={
            "sources/1. Модуль/media/dup.png": png_bytes(2, 2), "sources/1. Модуль/2. Раздел/Под/1. П.md": "# П\n",
            "sources/1. Модуль/2. Раздел/Под/media/dup.png": png_bytes(3, 3)})
        try:
            book.cfg.content.pages_beside_subdirs = True
            html, warnings = book.convert("1. Глубокий урок.md")
        finally:
            book.close()
        self.assertIn('src="../media/a.png"', html)
        self.assertIn('src="media/b.png"', html)
        self.assertTrue(any("неоднозначное встраивание ![[dup.png]]" in w for w in warnings), warnings)
        self.assertTrue(any("встраивание ![[nope.png|Нет]]: файла нет" in w for w in warnings), warnings)
        self.assertIn('<img alt="Нет" src="media/nope.png" title="Нет" />', html)  # аудит покажет «нет файла»

    def test_embed_in_callout(self):
        html, _ = self.convert("# Урок\n\n> [!note] Заметка\n> ![[a.png|В выноске]]\n")
        self.assertIn('<aside class="callout', html)
        self.assertIn('<figure class="md-figure">\n  <img class="md-media md-zoom" src="media/a.png" alt="В выноске"', html)

    def test_untouched_images(self):
        html, _ = self.convert("# Урок\n\n![внешняя](https://example.org/x.png)\n\n![чужая](other/x.png)\n")
        self.assertIn('<p><img alt="внешняя" src="https://example.org/x.png" /></p>', html)
        self.assertIn('<p><img alt="чужая" src="other/x.png" /></p>', html)

    def test_figures_and_lightbox_off(self):
        html, _ = self.convert("# Урок\n\n![a](media/a.png \"П\")\n", extra_toml="figures = false\nlightbox = false\n")
        self.assertIn('<p><img class="md-media" src="media/a.png" alt="a" width="40" height="20" loading="lazy" '
                      'decoding="async" title="П"></p>', html)

    def test_disabled_keeps_previous_output(self):
        book = MediaBook("# Урок\n\n![a](media/a.png)\n\n![[a.png|x]]\n")
        try:
            book.cfg.media.enabled = False
            book.cfg.content.pages_beside_subdirs = True      # иначе media/ — подкаталог рядом со страницами
            html, _ = book.convert()
        finally:
            book.close()
        self.assertIn('<p><img alt="a" src="media/a.png" /></p>', html)
        self.assertIn('!<span class="wikilink-unresolved"', html)
        self.assertNotIn("md-", html)


class BuildMediaTest(unittest.TestCase):
    def test_copy_credits_page_and_assets(self):
        book = MediaBook("# Урок\n\n![a](media/a.png)\n\n![[scheme.svg|С]]\n\n![](media/pd.gif)\n",
                         deep="# Глубокий\n\n![b](media/b.png)\n",
                         extra_toml='credits_page = "illustrations.html"\n',
                         files={"sources/1. Модуль/media/notes.txt": "не изображение"})
        try:
            self.assertEqual(book.build(strict=True), [])
            d = book.dist
            for rel, src in (("docs/01-modul/media/a.png", "sources/1. Модуль/media/a.png"),
                             ("docs/01-modul/2-razdel/media/b.png", "sources/1. Модуль/2. Раздел/media/b.png")):
                with open(os.path.join(d, rel), "rb") as a, open(os.path.join(book.root, src), "rb") as b:
                    self.assertEqual(a.read(), b.read())
            self.assertFalse(os.path.exists(os.path.join(d, "docs/01-modul/media/credits.toml")))
            self.assertFalse(os.path.exists(os.path.join(d, "docs/01-modul/media/notes.txt")))
            self.assertTrue(os.path.isfile(os.path.join(d, "assets/media.css")))
            with open(os.path.join(d, "docs/01-modul/1-urok.html"), encoding="utf-8") as fp:
                page = fp.read()
            self.assertIn('<link rel="stylesheet" href="../../assets/media.css?v=', page)
            self.assertIn('<script src="../../assets/media.js?v=', page)
            self.assertIn('id="md-lightbox"', page)
            self.assertIn('<p class="md-credits-link"><a href="../../illustrations.html">Иллюстрации и лицензии</a></p>', page)
            with open(os.path.join(d, "illustrations.html"), encoding="utf-8") as fp:
                credits = fp.read()
            self.assertIn('<span class="meta-tag module-tag">Справка</span>', credits)
            self.assertIn("<code>1. Модуль/2. Раздел/media/b.png</code>", credits)
            self.assertIn('Страницы: <a href="docs/01-modul/2-razdel/1-glubokiy-urok.html">Глубокий</a>', credits)
            self.assertIn("собственная иллюстрация книги", credits)
            with open(os.path.join(d, "index.html"), encoding="utf-8") as fp:
                self.assertIn('<a href="./illustrations.html">', fp.read())
            first = {}
            for root, _, files in os.walk(d):
                for f in files:
                    with open(os.path.join(root, f), "rb") as fp:
                        first[os.path.relpath(os.path.join(root, f), d)] = fp.read()
            book.build()                                   # воспроизводимость: вторая сборка побайтно та же
            for rel, data in first.items():
                with open(os.path.join(d, rel), "rb") as fp:
                    self.assertEqual(fp.read(), data, rel)
        finally:
            book.close()

    def test_disabled_book_gets_no_media_files(self):
        book = MediaBook("# Урок\n\n![a](media/a.png)\n")
        try:
            book.cfg.media.enabled = False
            book.cfg.content.pages_beside_subdirs = True      # иначе media/ — подкаталог рядом со страницами
            with contextlib.redirect_stdout(io.StringIO()):
                build(book.cfg, dist_dir=book.dist, is_pilot=False)
            self.assertFalse(os.path.exists(os.path.join(book.dist, "assets/media.css")))
            self.assertFalse(os.path.exists(os.path.join(book.dist, "assets/media.js")))
            self.assertFalse(os.path.exists(os.path.join(book.dist, "docs/01-modul/media")))
        finally:
            book.close()

    def test_credits_page_collision_and_bad_credits(self):
        book = MediaBook("# Урок\n", extra_toml='credits_page = "docs/01-modul/1-urok.html"\n')
        try:
            with self.assertRaisesRegex(BuildError, "занят страницей"):
                book.build()
        finally:
            book.close()
        book = MediaBook("# Урок\n", files={"sources/1. Модуль/media/credits.toml": '["a.png"]\nlicence = "PD"\n'})
        try:
            with self.assertRaisesRegex(MediaError, "неизвестные ключи"):
                book.build()
        finally:
            book.close()


if __name__ == "__main__":
    unittest.main()
