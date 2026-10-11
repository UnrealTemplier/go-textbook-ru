"""
engine/themes.py
Темы оформления: манифест engine/assets/themes/manifest.json.

Все темы манифеста доступны каждой книге: переключатель, CSS и ассеты.
"""

import json
import os
from typing import List, Tuple

THEMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "themes")

_FALLBACK_THEMES = [
    {"key": "paper", "label": "Paper", "icon": "document"},
    {"key": "light", "label": "Light", "icon": "sun"},
    {"key": "amber", "label": "Amber", "icon": "moon"},
]


def read_manifest() -> Tuple[str, List[dict]]:
    """Тема по умолчанию и все темы манифеста."""
    try:
        with open(os.path.join(THEMES_DIR, "manifest.json"), encoding="utf-8") as f:
            data = json.load(f)
        return data.get("default", "amber"), data.get("themes", [])
    except Exception:
        return "amber", _FALLBACK_THEMES


def active_themes() -> Tuple[str, List[dict]]:
    """Тема по умолчанию и все темы книги в порядке переключателя."""
    default, themes = read_manifest()
    return default, sorted(themes, key=lambda t: t.get("order", 99))
