"""
engine/hooks.py
Хуки книги (анализ § 4.3): book/hooks.py (путь — [layout] hooks_file) может определить любые из:

  transform_markdown(text, article) -> str      исходный Markdown статьи до конвертации
  render_callout(type, title, html) -> str|None  HTML выноски (None — оставить как есть)
  page_context(article, ctx) -> None             подстановки частичных шаблонов страницы
                                                 (article = None для главной); меняет ctx на месте
  extra_audit_checks(dist_dir) -> list[str]      дополнительные ошибки аудита

Остальные имена модуля движок не трогает.
"""

import importlib.util
import os

HOOK_NAMES = ("transform_markdown", "render_callout", "page_context", "extra_audit_checks")


class Hooks:
    def __init__(self, module=None):
        self.module = module

    def _get(self, name):
        return getattr(self.module, name, None) if self.module else None

    def transform_markdown(self, text, article):
        f = self._get("transform_markdown")
        return f(text, article) if f else text

    def render_callout(self, c_type, title, html_text):
        f = self._get("render_callout")
        if f:
            out = f(c_type, title, html_text)
            if out is not None:
                return out
        return html_text

    def page_context(self, article, ctx):
        f = self._get("page_context")
        if f:
            f(article, ctx)

    def extra_audit_checks(self, dist_dir):
        f = self._get("extra_audit_checks")
        return list(f(dist_dir)) if f else []


def load_hooks(config) -> Hooks:
    """Хуки книги, загруженные один раз на конфиг; без файла — пустые."""
    cached = getattr(config, "_hooks", None)
    if cached is not None:
        return cached
    path = config.path(config.layout.hooks_file) if config.layout.hooks_file else ""
    module = None
    if path and os.path.isfile(path):
        spec = importlib.util.spec_from_file_location("book_hooks", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    config._hooks = Hooks(module)
    return config._hooks
