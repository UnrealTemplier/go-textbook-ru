"""
engine/media.py
Изображения уроков ([media] в book.toml): папки media/ рядом со страницами, их файлы и атрибуция.

Только стандартная библиотека: размеры читаются из заголовков файлов (PNG, JPEG, GIF, WebP, SVG,
AVIF), credits.toml — tomllib. Порядок файлов детерминирован (обход сканера, natural_sort_key).
"""

import html
import os
import re
import shutil
import struct
import tomllib
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

Size = Tuple[int, int]


class MediaError(ValueError):
    """Ошибка в credits.toml (разбор, неизвестный ключ, неверный тип)."""


# ---------------------------------------------------------------------------
# Размеры изображений из заголовков
# ---------------------------------------------------------------------------
def _png_size(data: bytes) -> Optional[Size]:
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR" and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    return None


def _gif_size(data: bytes) -> Optional[Size]:
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    return None


def _exif_orientation(seg: bytes) -> int:
    """Тег 0x0112 (Orientation) из сегмента APP1 Exif; 1, если его нет."""
    if seg[:6] != b"Exif\x00\x00" or len(seg) < 14:
        return 1
    tiff = seg[6:]
    order = {b"II": "<", b"MM": ">"}.get(tiff[:2])
    if order is None:
        return 1
    try:
        (ifd,) = struct.unpack(order + "I", tiff[4:8])
        (count,) = struct.unpack(order + "H", tiff[ifd:ifd + 2])
        for i in range(count):
            entry = tiff[ifd + 2 + 12 * i:ifd + 14 + 12 * i]
            tag, typ = struct.unpack(order + "HH", entry[:4])
            if tag == 0x0112 and typ == 3:
                return struct.unpack(order + "H", entry[8:10])[0]
    except struct.error:
        pass
    return 1


def _jpeg_size(data: bytes) -> Optional[Size]:
    """Маркеры SOFn (кроме DHT C4, JPG C8, DAC CC); Exif-поворот 5–8 меняет стороны местами,
    как это делает браузер (image-orientation: from-image)."""
    if data[:2] != b"\xff\xd8":
        return None
    pos, orientation = 2, 1
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            return None
        marker = data[pos + 1]
        if marker == 0xFF:              # заполнитель
            pos += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        (length,) = struct.unpack(">H", data[pos + 2:pos + 4])
        if marker == 0xE1:
            orientation = _exif_orientation(data[pos + 4:pos + 2 + length])
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            if pos + 9 > len(data):
                return None
            h, w = struct.unpack(">HH", data[pos + 5:pos + 9])
            return (h, w) if orientation in (5, 6, 7, 8) else (w, h)
        if marker == 0xDA:              # начало данных скана без SOF — файл испорчен
            return None
        pos += 2 + length
    return None


def _webp_size(data: bytes) -> Optional[Size]:
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None                     # короткие куски: struct.error и IndexError ловит image_size
    chunk = data[12:16]
    if chunk == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
        w, h = struct.unpack("<HH", data[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if chunk == b"VP8L" and data[20] == 0x2F:
        (bits,) = struct.unpack("<I", data[21:25])
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8X" and len(data) >= 30:
        w = int.from_bytes(data[24:27], "little") + 1
        h = int.from_bytes(data[27:30], "little") + 1
        return w, h
    return None


def _iso_boxes(data: bytes, start: int, end: int):
    """Боксы ISOBMFF: (тип, начало содержимого, конец)."""
    pos = start
    while pos + 8 <= end:
        size, typ = struct.unpack(">I4s", data[pos:pos + 8])
        head = 8
        if size == 1:
            if pos + 16 > end:
                return
            (size,) = struct.unpack(">Q", data[pos + 8:pos + 16])
            head = 16
        elif size == 0:
            size = end - pos
        if size < head or pos + size > end:
            return
        yield typ, pos + head, pos + size
        pos += size


def _avif_size(data: bytes) -> Optional[Size]:
    """ftyp с брендом avif/avis → meta → iprp → ipco → ispe; из нескольких ispe (сетка плиток)
    берётся наибольший — это размер всего изображения. Поворот irot не учитывается."""
    boxes = list(_iso_boxes(data, 0, len(data)))
    if not boxes or boxes[0][0] != b"ftyp":
        return None
    _, a, b = boxes[0]
    brands = [data[a:a + 4]] + [data[i:i + 4] for i in range(a + 8, b, 4)]
    if not any(br in (b"avif", b"avis") for br in brands):
        return None
    best = None
    for typ, a, b in boxes:
        if typ != b"meta":
            continue
        for t2, a2, b2 in _iso_boxes(data, a + 4, b):          # meta — full box: 4 байта версии и флагов
            if t2 != b"iprp":
                continue
            for t3, a3, b3 in _iso_boxes(data, a2, b2):
                if t3 != b"ipco":
                    continue
                for t4, a4, b4 in _iso_boxes(data, a3, b3):
                    if t4 == b"ispe" and b4 - a4 >= 12:
                        w, h = struct.unpack(">II", data[a4 + 4:a4 + 12])
                        if best is None or w * h > best[0] * best[1]:
                            best = (w, h)
    return best


_SVG_TAG_RE = re.compile(r"<svg\b([^>]*)>", re.S)
_SVG_LENGTH_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*(px)?\s*$")


def _svg_attr(attrs: str, name: str) -> Optional[str]:
    m = re.search(r"(?:^|\s)" + name + r"\s*=\s*([\"'])(.*?)\1", attrs, re.S)
    return m.group(2) if m else None


def _svg_size(data: bytes) -> Optional[Size]:
    """width/height корневого <svg> в px (или без единиц); иначе — по viewBox. Проценты, em и т. п. —
    по viewBox, с пропорцией из него."""
    text = data[:65536].decode("utf-8", errors="ignore")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    m = _SVG_TAG_RE.search(text)
    if not m:
        return None
    attrs = m.group(1)
    lengths = []
    for name in ("width", "height"):
        value = _svg_attr(attrs, name)
        lm = _SVG_LENGTH_RE.match(value) if value is not None else None
        lengths.append(float(lm.group(1)) if lm else None)
    vb = _svg_attr(attrs, "viewBox")
    vb_size = None
    if vb:
        parts = [p for p in re.split(r"[\s,]+", vb.strip()) if p]
        try:
            if len(parts) == 4 and float(parts[2]) > 0 and float(parts[3]) > 0:
                vb_size = (float(parts[2]), float(parts[3]))
        except ValueError:
            pass
    w, h = lengths
    if w and h:
        return round(w), round(h)
    if vb_size:
        if w:
            return round(w), round(w * vb_size[1] / vb_size[0])
        if h:
            return round(h * vb_size[0] / vb_size[1]), round(h)
        return round(vb_size[0]), round(vb_size[1])
    return None


_READERS = {"png": _png_size, "gif": _gif_size, "jpg": _jpeg_size, "jpeg": _jpeg_size,
            "webp": _webp_size, "svg": _svg_size, "avif": _avif_size}


def image_size(path: str) -> Optional[Size]:
    """(ширина, высота) из заголовка файла; None — формат не распознан или заголовок не разобран.

    Формат определяется по расширению, затем по сигнатуре (на случай неверного расширения).
    """
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    try:
        with open(path, "rb") as fp:
            data = fp.read() if ext in ("svg", "avif", "jpg", "jpeg") else fp.read(64)
    except OSError:
        return None
    first = _READERS.get(ext)
    readers = ([first] if first else []) + [r for r in _READERS.values() if r is not first]
    for reader in readers:
        try:
            size = reader(data)
        except (struct.error, IndexError, ValueError):
            size = None
        if size and size[0] > 0 and size[1] > 0:
            return int(size[0]), int(size[1])
    return None


# ---------------------------------------------------------------------------
# Атрибуция и лицензии
# ---------------------------------------------------------------------------
CREDIT_KEYS = {"caption": str, "alt": str, "author": str, "license": str, "license_url": str,
               "source": str, "modified": str, "invert_dark": bool}


def load_credits(path: str) -> Dict[str, Dict[str, object]]:
    """credits.toml: таблица на файл (["имя.webp"]) с ключами CREDIT_KEYS; иначе — MediaError."""
    try:
        with open(path, "rb") as fp:
            data = tomllib.load(fp)
    except tomllib.TOMLDecodeError as e:
        raise MediaError(f"{path}: {e}")
    out = {}
    for name, entry in data.items():
        if not isinstance(entry, dict):
            raise MediaError(f'{path}: ["{name}"] — ожидается таблица (заголовок ["{name}"] и ключи под ним)')
        unknown = sorted(set(entry) - set(CREDIT_KEYS))
        if unknown:
            raise MediaError(f'{path}: ["{name}"]: неизвестные ключи {unknown} (допустимы {sorted(CREDIT_KEYS)})')
        for key, value in entry.items():
            if not isinstance(value, CREDIT_KEYS[key]):
                kind = "true или false" if CREDIT_KEYS[key] is bool else "строка"
                raise MediaError(f'{path}: ["{name}"].{key}: ожидается {kind}')
        out[name] = entry
    return out


def normalize_license(name: str) -> str:
    """«cc-by-sa 4.0» → «CC BY SA 4.0»: регистр, дефисы и подчёркивания не важны."""
    return " ".join(re.split(r"[\s_-]+", name.strip().upper())).strip()


_VERSION_TAIL_RE = re.compile(r"^\d+(\.\d+)*( [A-Z]{2,5})?$")


def license_allowed(license: str, allowed: List[str]) -> bool:
    """Лицензия из белого списка: то же имя или имя с версией и, возможно, кодом юрисдикции
    («CC BY 4.0», «CC BY-SA 3.0 DE» для «CC BY» и «CC BY-SA»). «CC BY-NC 4.0» под «CC BY» не подходит."""
    lic = normalize_license(license)
    for a in allowed:
        na = normalize_license(a)
        if lic == na:
            return True
        if lic.startswith(na + " ") and _VERSION_TAIL_RE.match(lic[len(na) + 1:]):
            return True
    return False


def is_own(credit: Optional[Dict[str, object]]) -> bool:
    return bool(credit) and normalize_license(str(credit.get("license", ""))) == "OWN"


# ---------------------------------------------------------------------------
# Библиотека медиа книги
# ---------------------------------------------------------------------------
def _natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


class MediaFile:
    def __init__(self, src_path: str, rel_path: str, dist_rel: str, folder: "MediaFolder"):
        self.src_path = src_path          # абсолютный путь исходника
        self.rel_path = rel_path          # путь от content.root через '/', например «1. Основы/media/x.png»
        self.dist_rel = dist_rel          # путь в dist/, например «docs/01-osnovy/media/x.png»
        self.folder = folder
        self.name = os.path.basename(src_path)
        self.size_bytes = os.path.getsize(src_path)
        self._size: Optional[Size] = None
        self._size_read = False

    @property
    def size(self) -> Optional[Size]:
        if not self._size_read:
            self._size = image_size(self.src_path)
            self._size_read = True
        return self._size

    @property
    def credit(self) -> Optional[Dict[str, object]]:
        return self.folder.credits.get(self.name)

    def __repr__(self):
        return f"MediaFile({self.rel_path!r})"


class MediaFolder:
    def __init__(self, src_dir: str, dist_dir: str, credits_path: Optional[str]):
        self.src_dir = src_dir            # абсолютный путь папки media/
        self.dist_dir = dist_dir          # её путь в dist/
        self.credits_path = credits_path  # credits.toml или None
        self.credits: Dict[str, Dict[str, object]] = load_credits(credits_path) if credits_path else {}
        self.files: List[MediaFile] = []
        self.skipped: List[str] = []      # файлы с расширением не из extensions: в dist/ не попадают


class MediaLibrary:
    """Все папки media/ книги: файлы, атрибуция, поиск по пути и по имени."""

    def __init__(self, sources_dir: str, folders: List[Tuple[str, str]], config):
        """folders — пары (абсолютный путь каталога со страницами, его путь в dist/) в порядке обхода сканера."""
        self.config = config
        m = config.media
        self.sources_dir = os.path.abspath(sources_dir)
        self.folders: List[MediaFolder] = []
        self.files: List[MediaFile] = []
        self.by_src: Dict[str, MediaFile] = {}
        self.by_name: Dict[str, List[MediaFile]] = {}
        exts = set(m.extensions)
        for page_dir, dist_dir in folders:
            src = os.path.join(page_dir, m.dir_name)
            if not os.path.isdir(src):
                continue
            credits = os.path.join(src, m.credits_file)
            folder = MediaFolder(src, f"{dist_dir}/{m.dir_name}", credits if os.path.isfile(credits) else None)
            self.folders.append(folder)
            for root, dirs, names in os.walk(src):
                dirs.sort(key=_natural_key)
                rel_dir = os.path.relpath(root, src).replace(os.sep, "/")
                for name in sorted(names, key=_natural_key):
                    path = os.path.join(root, name)
                    if root == src and name == m.credits_file:
                        continue
                    if os.path.splitext(name)[1].lower().lstrip(".") not in exts:
                        folder.skipped.append(path)
                        continue
                    sub = "" if rel_dir == "." else rel_dir + "/"
                    f = MediaFile(path, os.path.relpath(path, self.sources_dir).replace(os.sep, "/"),
                                  f"{folder.dist_dir}/{sub}{name}", folder)
                    folder.files.append(f)
                    self.files.append(f)
                    self.by_src[self._key(path)] = f
                    self.by_name.setdefault(name, []).append(f)

    @staticmethod
    def _key(path: str) -> str:
        return os.path.normcase(os.path.normpath(os.path.abspath(path)))

    def lookup(self, path: str) -> Optional[MediaFile]:
        """Файл медиа по пути исходника (любой регистр разделителей, «..» допустимы)."""
        return self.by_src.get(self._key(path))

    def find_embed(self, target: str, page_dir: str) -> List[MediaFile]:
        """Кандидаты для ![[target]]: сначала media/ страницы, затем вся книга (по имени или концу пути)."""
        own = self.lookup(os.path.join(page_dir, self.config.media.dir_name, target))
        if own is not None:
            return [own]
        t = target.strip().strip("/")
        if "/" in t:
            near = self.lookup(os.path.join(page_dir, t))
            if near is not None:
                return [near]
            return [f for f in self.files if f.rel_path == t or f.rel_path.endswith("/" + t)]
        return list(self.by_name.get(t, []))

    def copy_to(self, dist_dir: str) -> int:
        """Побайтное копирование в dist/ в порядке обхода; возвращает число файлов."""
        for f in self.files:
            dst = os.path.join(dist_dir, f.dist_rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(f.src_path, dst)
        return len(self.files)

    @property
    def total_bytes(self) -> int:
        return sum(f.size_bytes for f in self.files)


def library_for(scanner) -> Optional[MediaLibrary]:
    """Библиотека медиа просканированной книги (создаётся один раз); None — [media] выключен."""
    if scanner is None or not scanner.config.media.enabled:
        return None
    if scanner.media is None:
        scanner.media = MediaLibrary(scanner.sources_dir, scanner.media_dirs, scanner.config)
    return scanner.media


# ---------------------------------------------------------------------------
# HTML: <img>, <figure>, строка атрибуции
# ---------------------------------------------------------------------------
def credit_html(credit: Optional[Dict[str, object]], config, full: bool = False) -> str:
    """Строка атрибуции: автор · лицензия · источник · изменения (строки — [media] в strings).

    Лицензия own в подписи не выводится; full=True (страница «Иллюстрации и лицензии») — выводится.
    """
    if not credit:
        return ""
    esc = lambda v: html.escape(str(v))
    parts = []
    if credit.get("author"):
        parts.append(config.t("media.author", author=esc(credit["author"])))
    lic = str(credit.get("license", "")).strip()
    if lic and normalize_license(lic) == "OWN" and full:
        parts.append(config.t("media.license_own"))
    elif lic and normalize_license(lic) != "OWN":
        label = config.t("media.license_pd") if normalize_license(lic) == "PD" else esc(lic)
        if credit.get("license_url"):
            label = f'<a href="{esc(credit["license_url"])}" rel="license">{label}</a>'
        parts.append(label)
    if credit.get("source"):
        parts.append(f'<a href="{esc(credit["source"])}">{config.t("media.source")}</a>')
    if credit.get("modified"):
        parts.append(config.t("media.modified", modified=esc(credit["modified"])))
    return " · ".join(parts)


def media_src(f: MediaFile, page_rel: str) -> str:
    """Путь к файлу медиа от страницы dist/ (page_rel — путь страницы от корня сайта)."""
    rel = os.path.relpath(f.dist_rel, os.path.dirname(page_rel) or ".").replace(os.sep, "/")
    return quote(rel)


def img_tag(f: MediaFile, page_rel: str, alt: str, config, title: str = "") -> str:
    """<img> файла медиа: размеры из заголовка, отложенная загрузка, классы увеличения и инверсии."""
    classes = ["md-media"]
    if config.media.lightbox:
        classes.append("md-zoom")
    credit = f.credit or {}
    if credit.get("invert_dark"):
        classes.append("md-invert-dark")
    size = f.size
    dims = f' width="{size[0]}" height="{size[1]}"' if size else ""
    title_attr = f' title="{html.escape(title)}"' if title else ""
    return (f'<img class="{" ".join(classes)}" src="{html.escape(media_src(f, page_rel))}" alt="{html.escape(alt)}"'
            f'{dims} loading="lazy" decoding="async"{title_attr}>')


def caption_and_alt(f: MediaFile, alt: str, title: str) -> Tuple[str, str]:
    """Подпись (title из Markdown, иначе caption из credits.toml) и alt (из текста, иначе alt или
    подпись из credits.toml)."""
    credit = f.credit or {}
    caption = title or str(credit.get("caption", ""))
    return caption, alt or str(credit.get("alt", "")) or caption


def figure_html(f: MediaFile, page_rel: str, alt: str, title: str, config) -> str:
    caption, alt = caption_and_alt(f, alt, title)
    credit = credit_html(f.credit, config)
    parts = [html.escape(caption)] if caption else []
    if credit:
        parts.append(f'<span class="md-credit">{credit}</span>')
    figcaption = f'\n  <figcaption>{" ".join(parts)}</figcaption>' if parts else ""
    return f'<figure class="md-figure">\n  {img_tag(f, page_rel, alt, config)}{figcaption}\n</figure>'


def credits_page_html(library: MediaLibrary, usage: Dict[MediaFile, list], page_rel: str, config) -> str:
    """Тело служебной страницы «Иллюстрации и лицензии»: все файлы медиа книги в порядке обхода."""
    items = []
    for f in library.files:
        caption, alt = caption_and_alt(f, "", "")
        credit = credit_html(f.credit, config, full=True)
        pages = usage.get(f, [])
        links = ", ".join(
            f'<a href="{html.escape(os.path.relpath(a.rel_output_path, os.path.dirname(page_rel) or ".").replace(os.sep, "/"))}">'
            f'{html.escape(a.title)}</a>' for a in pages) or config.t("media.credits_unused")
        rows = [f'<p class="md-credits-name"><code>{html.escape(f.rel_path)}</code></p>']
        if caption:
            rows.append(f"<p>{html.escape(caption)}</p>")
        if credit:
            rows.append(f'<p class="md-credit">{credit}</p>')
        rows.append(f'<p class="md-credits-pages">{config.t("media.credits_pages")} {links}</p>')
        items.append(f'<li class="md-credits-item">\n  <div class="md-credits-thumb">{img_tag(f, page_rel, alt, config)}</div>\n'
                     f'  <div class="md-credits-info">\n    ' + "\n    ".join(rows) + "\n  </div>\n</li>")
    return (f'<p>{config.t("media.credits_intro", n=len(library.files))}</p>\n'
            '<ul class="md-credits-list">\n' + "\n".join(items) + "\n</ul>\n")
