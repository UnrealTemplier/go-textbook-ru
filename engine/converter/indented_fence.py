"""
engine/converter/indented_fence.py
Ограды кода с отступом внутри списков (U13, анализ § 4.7.3, Приложение А.2).

Python-Markdown распознаёт ограду только с начала строки, поэтому ограда внутри пункта списка
выводится inline-кодом. Препроцессор (приоритет 24: после fenced_code_block = 25, выше
html_block = 20) прячет такой блок в htmlStash. Плейсхолдер — отдельный блок на отступе самой
ограды; перевод отступов Obsidian → Python-Markdown делает только препроцессор списков, поэтому
включать ограды без списков запрещено (проверяет config.py).
"""

import markdown
from markdown.preprocessors import Preprocessor

from .code_mask import scan_indented_fences


class IndentedFencePreprocessor(Preprocessor):
    def __init__(self, md, warn_func=None):
        super().__init__(md)
        self.warn = warn_func or (lambda msg: None)

    @staticmethod
    def _escape_code(text: str) -> str:
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    def run(self, lines):
        blocks = {b['start_line']: b for b in scan_indented_fences(lines, self.warn)}
        out, i, n = [], 0, len(lines)
        while i < n:
            b = blocks.get(i)
            if b is None:
                out.append(lines[i])
                i += 1
                continue
            code = '\n'.join(b['code_lines']) + '\n' if b['code_lines'] else ''   # байты как у fenced_code
            lang = f' class="language-{b["lang"]}"' if b['lang'] else ''
            ph = self.md.htmlStash.store(f'<pre><code{lang}>{self._escape_code(code)}</code></pre>')
            if out and out[-1].strip():
                out.append('')                      # плейсхолдер — отдельный блок, а не строка абзаца
            out.append(b['open_indent'] + ph)       # отступ ограды; перевод отступов — препроцессор списков
            nxt = b['end_line'] + 1
            if nxt < n and lines[nxt].strip():
                out.append('')
            i = nxt
        return out


class IndentedFenceExtension(markdown.Extension):
    def __init__(self, warn_func=None):
        super().__init__()
        self.warn_func = warn_func

    def extendMarkdown(self, md):
        md.preprocessors.register(IndentedFencePreprocessor(md, self.warn_func), "indented_fence", 24)
