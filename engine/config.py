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


@dataclass
class ReadingTimeConfig:
    method: str = "bytes"
    divisor: int = 800
    min: int = 2


@dataclass
class NavigationConfig:
    reading_time: ReadingTimeConfig = field(default_factory=ReadingTimeConfig)


@dataclass
class BookConfig:
    project: ProjectConfig = field(default_factory=ProjectConfig)
    content: ContentConfig = field(default_factory=ContentConfig)
    slug: SlugConfig = field(default_factory=SlugConfig)
    callouts: CalloutsConfig = field(default_factory=CalloutsConfig)
    navigation: NavigationConfig = field(default_factory=NavigationConfig)
    # Каталог, относительно которого заданы пути конфига (каталог book.toml)
    root_dir: str = "."

    def path(self, rel: str) -> str:
        return rel if os.path.isabs(rel) else os.path.join(self.root_dir, rel)

    def storage_key(self, name: str) -> str:
        return self.project.storage_prefix + name


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
    for pat in cfg.content.clean_cliches:
        try:
            re.compile(pat)
        except re.error as e:
            raise ConfigError(f"content.clean_cliches: неверное выражение {pat!r}: {e}")
    sub = cfg.slug.subsection
    if not (isinstance(sub, (list, tuple)) and len(sub) == 2):
        raise ConfigError("slug.subsection: ожидается пара длин [N, M]")
    cfg.slug.subsection = tuple(sub)
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


def canonicalize_title(title: str, replacements) -> str:
    """Канонические названия: упорядоченные замены целых слов (например, net_http → net/http)."""
    for src, dst in replacements:
        title = re.sub(r"\b" + re.escape(src) + r"\b", lambda _m, d=dst: d, title)
    return title
