"""
engine/converter/math_protect.py
Защита формул от Python-Markdown (анализ § 4.7.5, Приложение А.5).

Python-Markdown превращает \\( … \\) в ( … ), съедает \\_ и делает курсив из _ и * внутри
формул. Inline-процессор (приоритет 185: после backtick = 190, до escape = 180 и em_strong)
прячет формулу целиком, с разделителями, в htmlStash после html.escape. Разделители берутся
из [math].protect (левые) и их пар в [math].delimiters.
"""

import html
import re

import markdown
import markdown.util as util
from markdown.inlinepatterns import InlineProcessor


class MathInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        raw = m.group(0)
        if util.INLINE_PLACEHOLDER_PREFIX in raw or '\x02' in raw or '\x03' in raw:
            return None, None, None          # внутри формулы уже обработанный inline-код
        return self.md.htmlStash.store(html.escape(raw)), m.start(0), m.end(0)


class MathProtectExtension(markdown.Extension):
    def __init__(self, delimiters, protect):
        super().__init__()
        by_left = {d["left"]: d for d in delimiters}
        missing = [p for p in protect if p not in by_left]
        if missing:
            raise ValueError(f"[math].protect {missing} отсутствуют в [math].delimiters")
        self.pairs = [by_left[p] for p in protect]

    def extendMarkdown(self, md):
        for idx, d in enumerate(self.pairs):
            pattern = r"(?<!\\)" + re.escape(d["left"]) + r"(.+?)" + re.escape(d["right"])
            md.inlinePatterns.register(MathInlineProcessor(pattern, md), f"math_protect_{idx}", 185)
