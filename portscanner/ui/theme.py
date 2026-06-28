"""UI color palette."""

from __future__ import annotations

from typing import Final

ThemeColors = dict[str, str]

COLORS: Final[ThemeColors] = {
    "bg": "#0D1117",
    "surface": "#161B22",
    "surface_alt": "#1C2128",
    "accent": "#00FF88",
    "accent_dim": "#00AA55",
    "accent_hover": "#00CC6A",
    "danger": "#FF4444",
    "danger_hover": "#CC2222",
    "warning": "#FFB800",
    "text": "#E6EDF3",
    "text_muted": "#8B949E",
    "border": "#30363D",
    "table_bg": "#0D1117",
    "table_row": "#161B22",
    "heading": "#00AA55",
}
