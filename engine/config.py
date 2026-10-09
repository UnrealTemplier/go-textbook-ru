"""
engine/config.py
Загрузка и проверка конфигурации книги book.toml (анализ § 4.4).

Только стандартная библиотека: tomllib + dataclasses. Значения по умолчанию — нейтральные
значения движка; всё, что специфично для книги, задаётся в её book.toml. Неизвестный ключ —
ошибка (это почти всегда опечатка).
"""

import dataclasses
import os
import re
import tomllib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class ConfigError(ValueError):
    """Ошибка в book.toml."""


@dataclass
class ProjectConfig:
    storage_prefix: str = ""
    version: Optional[str] = None
    version_file: Optional[str] = None
    version_pattern: Optional[str] = None


@dataclass
class ContentConfig:
    root: str = "sources"
    # Упорядоченные пары [from, to]: from — целое слово (границы \b), заменяется на to
    canonical_replacements: List[Tuple[str, str]] = field(default_factory=list)
    # Регулярные выражения (IGNORECASE); совпадения удаляются из текста статьи при сборке
    clean_cliches: List[str] = field(default_factory=list)
    # "filename" — название страницы из имени файла; "h1" — из первого «# …», который убирается из тела
    title_source: str = "filename"
    # Регулярное выражение имени индексного файла каталога (U22), например "^0+\\. "; пусто — выключено
    index_file: str = ""
    # false — [[…]] не разбираются вовсе (в данных книги это не ссылки, например вывод программ)
    wikilinks: bool = True


@dataclass
class SlugConfig:
    module: int = 35
    section: int = 35
    subsection: Tuple[int, int] = (20, 25)
    page: int = 55
    anchor: int = 80


@dataclass
class CalloutsConfig:
    # «собеседован», «интервью», «interview» в заголовке выноски → оформление interview
    interview_heuristic: bool = False
    # Алиасы типов: {"critical": "note"}; неизвестный тип без алиаса — предупреждение (в --strict ошибка)
    alias: Dict[str, str] = field(default_factory=dict)


@dataclass
class ReadingTimeConfig:
    method: str = "bytes"
    divisor: int = 800
    min: int = 2


@dataclass
class NavigationConfig:
    reading_time: ReadingTimeConfig = field(default_factory=ReadingTimeConfig)
    # "static" — полный сайдбар в каждой странице; "hybrid" — в HTML только текущий модуль,
    # остальное — из assets/nav-data.js (анализ § 4.8.1)
    mode: str = "hybrid"
    # hybrid: заглушки остальных модулей в HTML (true) или только из nav-data.js (false)
    static_module_list: bool = True


@dataclass
class MarkdownConfig:
    # Списки в стиле Obsidian (U17): список сразу после абзаца, вложенность 2–3 пробела
    obsidian_lists: bool = False
    # Ограды кода с отступом внутри списков (U13); требует obsidian_lists
    indented_fences: bool = False


def _default_delimiters() -> List[Dict[str, Any]]:
    return [
        {"left": "$$", "right": "$$", "display": True},
        {"left": "$", "right": "$", "display": False},
        {"left": "\\(", "right": "\\)", "display": False},
        {"left": "\\[", "right": "\\]", "display": True},
    ]


@dataclass
class MathConfig:
    # Разделители KaTeX auto-render (передаются в браузер как есть)
    delimiters: List[Dict[str, Any]] = field(default_factory=_default_delimiters)
    # Левые разделители формул, которые защищаются от Python-Markdown (каждый — из delimiters)
    protect: List[str] = field(default_factory=list)
    ignored_tags: List[str] = field(default_factory=lambda: ["script", "noscript", "style", "textarea", "pre", "code", "option"])
    ignored_classes: List[str] = field(default_factory=lambda: ["code-block", "mermaid", "mermaid-wrapper"])


@dataclass
class FeaturesConfig:
    # Подключать Mermaid, KaTeX и Prism только на страницах, где они нужны (анализ § 4.8.3)
    conditional_scripts: bool = True


@dataclass
class LayoutConfig:
    # Пути — относительно каталога book.toml; отсутствующие файлы и каталоги просто не используются
    overrides_dir: str = "book/overrides"     # templates/<имя>.html и assets/<путь> заменяют файлы движка
    hooks_file: str = "book/hooks.py"
    extra_assets_dir: str = "book/assets"     # extra.css и extra.js подключаются после ассетов движка


@dataclass
class BrandingConfig:
    # Пути — относительно каталога book.toml; SVG вставляются в страницу как есть
    logo_icon_svg_file: str = ""
    logo_title_svg_file: str = ""
    logo_title_text: str = ""
    logo_sub: str = ""
    logo_aria_label: str = ""
    favicon_ico: str = ""
    favicon_svg: str = ""


@dataclass
class ArticlePageConfig:
    # Строки с суффиксом _html вставляются как HTML без экранирования
    title_suffix_html: str = ""
    # {title} — экранированное название статьи
    meta_description_html: str = "{title}"
    footer_html: List[str] = field(default_factory=list)


@dataclass
class IndexPageConfig:
    # Подстановки: {modules}, {articles}, {articles_grouped} («1 413»), {mermaid}
    title_html: str = ""
    meta_description_html: str = ""
    hero_badge_html: str = ""
    hero_title_html: str = ""
    quote_html: str = ""
    quote_author_html: str = ""
    search_placeholder: str = ""
    stats: List[Dict[str, str]] = field(default_factory=list)          # [{value, label}]
    catalog_title_html: str = ""
    catalog_sub_html: str = ""
    roadmap_title_html: str = ""
    roadmap_steps: List[Dict[str, str]] = field(default_factory=list)  # [{badge, title_html, text_html}]
    footer_html: List[str] = field(default_factory=list)


@dataclass
class BookConfig:
    project: ProjectConfig = field(default_factory=ProjectConfig)
    content: ContentConfig = field(default_factory=ContentConfig)
    slug: SlugConfig = field(default_factory=SlugConfig)
    callouts: CalloutsConfig = field(default_factory=CalloutsConfig)
    navigation: NavigationConfig = field(default_factory=NavigationConfig)
    markdown: MarkdownConfig = field(default_factory=MarkdownConfig)
    math: MathConfig = field(default_factory=MathConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    branding: BrandingConfig = field(default_factory=BrandingConfig)
    article_page: ArticlePageConfig = field(default_factory=ArticlePageConfig)
    index_page: IndexPageConfig = field(default_factory=IndexPageConfig)
    # Оверлеи навигации (траектории): [{title, modules = [номера модулей]}]; модуль может входить
    # в несколько оверлеев или ни в один
    overlays: List[Dict[str, Any]] = field(default_factory=list)
    # Переопределения строк интерфейса движка (engine/strings/ru.toml), та же структура
    strings: Dict[str, Any] = field(default_factory=dict)
    # Каталог, относительно которого заданы пути конфига (каталог book.toml)
    root_dir: str = "."

    def path(self, rel: str) -> str:
        return rel if os.path.isabs(rel) else os.path.join(self.root_dir, rel)

    def storage_key(self, name: str) -> str:
        return self.project.storage_prefix + name

    def t(self, key: str, **kw) -> str:
        """Строка интерфейса: 'раздел.ключ', подстановки {n} и т. п."""
        if not hasattr(self, "_ui"):
            self._ui = merge_strings(self.strings)
        text = self._ui[key]
        for name, value in kw.items():
            text = text.replace("{" + name + "}", str(value))
        return text


STRINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strings")


def _flatten(data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    out = {}
    for key, value in data.items():
        full = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, full + "."))
        else:
            out[full] = value
    return out


def default_strings(lang: str = "ru") -> Dict[str, str]:
    with open(os.path.join(STRINGS_DIR, f"{lang}.toml"), "rb") as fp:
        return _flatten(tomllib.load(fp))


def merge_strings(overrides: Dict[str, Any]) -> Dict[str, str]:
    """Строки движка + переопределения книги. Ключ, которого нет в движке, — ошибка (опечатка)."""
    ui = default_strings()
    flat = _flatten(overrides)
    unknown = sorted(set(flat) - set(ui))
    if unknown:
        raise ConfigError(f"strings: неизвестные ключи {unknown}")
    for key, value in flat.items():
        if not isinstance(value, str):
            raise ConfigError(f"strings.{key}: ожидается строка")
    ui.update(flat)
    return ui


def _build(cls, data: Dict[str, Any], where: str):
    """Собирает dataclass из таблицы TOML: неизвестный ключ — ошибка, вложенные таблицы — рекурсивно."""
    if not isinstance(data, dict):
        raise ConfigError(f"{where}: ожидается таблица")
    fields = {f.name: f for f in dataclasses.fields(cls) if f.name != "root_dir"}
    unknown = sorted(set(data) - set(fields))
    if unknown:
        raise ConfigError(f"{where}: неизвестные ключи {unknown}")
    kwargs = {}
    for name, value in data.items():
        f = fields[name]
        default = f.default_factory() if f.default_factory is not dataclasses.MISSING else f.default
        if dataclasses.is_dataclass(default):
            kwargs[name] = _build(type(default), value, f"{where}.{name}")
        else:
            kwargs[name] = value
    return cls(**kwargs)


def _validate(cfg: BookConfig) -> None:
    p = cfg.project
    if not re.fullmatch(r"[a-z0-9_]*", p.storage_prefix):
        raise ConfigError("project.storage_prefix: допустимы только a-z, 0-9 и '_'")
    if p.version and (p.version_file or p.version_pattern):
        raise ConfigError("project: укажите либо version, либо version_file + version_pattern")
    if bool(p.version_file) != bool(p.version_pattern):
        raise ConfigError("project: version_file и version_pattern задаются вместе")
    for pair in cfg.content.canonical_replacements:
        if not (isinstance(pair, (list, tuple)) and len(pair) == 2 and all(isinstance(x, str) for x in pair)):
            raise ConfigError(f"content.canonical_replacements: ожидается пара строк, получено {pair!r}")
    cfg.content.canonical_replacements = [tuple(p) for p in cfg.content.canonical_replacements]
    if cfg.content.title_source not in ("filename", "h1"):
        raise ConfigError("content.title_source: допустимо 'filename' или 'h1'")
    if cfg.content.index_file:
        try:
            re.compile(cfg.content.index_file)
        except re.error as e:
            raise ConfigError(f"content.index_file: неверное выражение: {e}")
    for pat in cfg.content.clean_cliches:
        try:
            re.compile(pat)
        except re.error as e:
            raise ConfigError(f"content.clean_cliches: неверное выражение {pat!r}: {e}")
    sub = cfg.slug.subsection
    if not (isinstance(sub, (list, tuple)) and len(sub) == 2):
        raise ConfigError("slug.subsection: ожидается пара длин [N, M]")
    cfg.slug.subsection = tuple(sub)
    for i, st in enumerate(cfg.index_page.stats):
        if not isinstance(st, dict) or set(st) != {"value", "label"}:
            raise ConfigError(f"index_page.stats[{i}]: ожидаются ключи value и label")
    for i, st in enumerate(cfg.index_page.roadmap_steps):
        if not isinstance(st, dict) or set(st) != {"badge", "title_html", "text_html"}:
            raise ConfigError(f"index_page.roadmap_steps[{i}]: ожидаются ключи badge, title_html, text_html")
    merge_strings(cfg.strings)
    for i, ov in enumerate(cfg.overlays):
        if (not isinstance(ov, dict) or set(ov) != {"title", "modules"} or not isinstance(ov["modules"], list)
                or not all(isinstance(n, int) for n in ov["modules"])):
            raise ConfigError(f"overlays[{i}]: ожидаются title и modules = [номера модулей]")
    for k, v in cfg.callouts.alias.items():
        if not isinstance(v, str):
            raise ConfigError(f"callouts.alias.{k}: ожидается имя типа выноски")
    cfg.callouts.alias = {k.lower(): v.lower() for k, v in cfg.callouts.alias.items()}
    if cfg.markdown.indented_fences and not cfg.markdown.obsidian_lists:
        raise ConfigError("markdown.indented_fences требует markdown.obsidian_lists = true: "
                          "без перевода отступов списков блок кода не попадёт в свой пункт")
    lefts = []
    for i, d in enumerate(cfg.math.delimiters):
        if not isinstance(d, dict) or set(d) != {"left", "right", "display"}:
            raise ConfigError(f"math.delimiters[{i}]: ожидаются ключи left, right, display")
        lefts.append(d["left"])
    missing = [p for p in cfg.math.protect if p not in lefts]
    if missing:
        raise ConfigError(f"math.protect: {missing} нет среди левых разделителей math.delimiters")
    if cfg.navigation.mode not in ("static", "hybrid"):
        raise ConfigError("navigation.mode: допустимо 'static' или 'hybrid'")
    if cfg.navigation.reading_time.method != "bytes":
        raise ConfigError("navigation.reading_time.method: поддерживается только 'bytes'")


def load_config(path: Optional[str] = None) -> BookConfig:
    """Читает book.toml. Без пути — book.toml в текущем каталоге; если его нет — значения по умолчанию."""
    if path is None:
        path = "book.toml"
        if not os.path.exists(path):
            return BookConfig(root_dir=os.path.abspath("."))
    with open(path, "rb") as fp:
        try:
            data = tomllib.load(fp)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"{path}: {e}")
    cfg = _build(BookConfig, data, os.path.basename(path))
    cfg.root_dir = os.path.dirname(os.path.abspath(path))
    _validate(cfg)
    return cfg


def read_text_asset(cfg: BookConfig, rel: str) -> str:
    """Текстовый ассет книги (например, SVG логотипа) без завершающих переводов строки."""
    if not rel:
        return ""
    with open(cfg.path(rel), encoding="utf-8") as fp:
        return fp.read().rstrip("\n")


def canonicalize_title(title: str, replacements) -> str:
    """Канонические названия: упорядоченные замены целых слов (например, net_http → net/http)."""
    for src, dst in replacements:
        title = re.sub(r"\b" + re.escape(src) + r"\b", lambda _m, d=dst: d, title)
    return title
