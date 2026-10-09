"""
engine/converter/callouts.py
Выноски как плейсхолдеры (А3а′, анализ § 4.7.7, Приложение А.3).

Сейчас выноски превращаются в HTML до основного прохода, и строчные препроцессоры видят их
HTML. С А3а′ выноска заменяется строкой <!--CALLOUT_PLACEHOLDER_N--> (как Mermaid), тело
рендерится отдельно: маска тела → wikilinks → md.convert. HTML <aside> — тот же, что сейчас.
"""

import re
from typing import Dict, List

from ..hooks import load_hooks
from .code_mask import UnifiedCodeLineMask

CALLOUT_START_RE = re.compile(r"^>\s*\[!([a-zA-Z0-9_-]+)\]\s*(.*)$")


class CalloutExtractor:
    def __init__(self, converter):
        self.converter = converter    # даёт md, config, _transform_wikilinks, callout_style, _callout_html

    def extract_callouts(self, text: str, placeholders: Dict[str, str], article) -> str:
        lines = text.splitlines()
        out: List[str] = []
        state = {"in": False, "type": "note", "title": "", "body": [], "idx": 0}

        def flush():
            ph = f"<!--CALLOUT_PLACEHOLDER_{state['idx']}-->"
            placeholders[ph] = self.render(state["type"], state["title"], state["body"], article)
            out.append(f"\n\n{ph}\n\n")
            state["idx"] += 1
            state["body"] = []

        i = 0
        while i < len(lines):
            line = lines[i]
            m = CALLOUT_START_RE.match(line)
            if m:
                if state["in"]:
                    flush()
                state.update({"in": True, "type": m.group(1).lower(), "title": m.group(2).strip()})
                i += 1
                continue
            if state["in"]:
                if line.startswith(">"):
                    content = line[1:]
                    state["body"].append(content[1:] if content.startswith(" ") else content)
                    i += 1
                    continue
                if line.strip() == "" and i + 1 < len(lines) and lines[i + 1].startswith(">"):
                    state["body"].append("")
                    i += 1
                    continue
                flush()
                state["in"] = False
                if line.strip() != "":
                    out.append(line)
                i += 1
                continue
            out.append(line)
            i += 1
        if state["in"]:
            flush()
        return "\n".join(out)

    def render(self, c_type: str, c_title: str, body_lines: List[str], article) -> str:
        conv = self.converter
        body = "\n".join(body_lines)
        mask = UnifiedCodeLineMask(body, conv.md, include_indented=conv.config.markdown.indented_fences)
        body = conv._transform_wikilinks(body, article, mask=mask)
        inner_html = conv.md.convert(body)       # heading_slugs здесь None: HeadingTreeprocessor пассивен
        conv.md.reset()
        cfg, title = conv.callout_style(c_type, c_title)
        return load_hooks(conv.config).render_callout(c_type, title, conv._callout_html(cfg, title, inner_html))
