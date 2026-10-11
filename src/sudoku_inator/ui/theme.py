"""Colour palettes and font helpers for light/dark themes.

All colours are Qt-compatible hex strings.  The minimum font size is 6pt
as specified in the product requirements.
"""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication


MIN_FONT_PT: int = 6
FONT_FAMILY: str = "Arial"


@dataclass(frozen=True)
class Palette:
    """A complete set of colours for one theme."""

    # Application chrome
    window_bg: str
    window_text: str
    base: str           # widget backgrounds (e.g. grids, inputs)
    alt_base: str       # alternating row colour
    text: str
    button_bg: str
    button_text: str
    highlight: str      # selected cell / item
    highlight_text: str

    # Sudoku-specific
    fixed_bg: str       # clue/given cell background
    fixed_text: str
    pencil_text: str    # pencil/candidate mark colour
    conflict_bg: str    # cell with a conflict
    peer_bg: str        # peer highlight (same row/col/box)
    border: str         # box/region border colour
    thin_border: str    # cell-to-cell border
    black_cell_bg: str  # Str8ts black cell background
    cage_member_bg: str # Killer cage member background tint
    cage_label_color: str  # Killer cage sum label colour
    cage_dash_pattern: tuple[float, ...]  # dash pattern for intra-cage thin edges


LIGHT = Palette(
    window_bg="#F5F5F5",
    window_text="#1A1A1A",
    base="#FFFFFF",
    alt_base="#EFEFEF",
    text="#1A1A1A",
    button_bg="#E0E0E0",
    button_text="#1A1A1A",
    highlight="#4A90D9",
    highlight_text="#FFFFFF",
    fixed_bg="#DDEEFF",
    fixed_text="#1A1A1A",
    pencil_text="#888888",
    conflict_bg="#FFD0D0",
    peer_bg="#EEF4FF",
    border="#333333",
    thin_border="#BBBBBB",
    black_cell_bg="#1a1a1a",
    cage_member_bg="#e8f4e8",
    cage_label_color="#2a6020",
    cage_dash_pattern=(4.0, 2.0),
)

DARK = Palette(
    window_bg="#1E1E1E",
    window_text="#D4D4D4",
    base="#252526",
    alt_base="#2D2D30",
    text="#D4D4D4",
    button_bg="#3A3A3C",
    button_text="#D4D4D4",
    highlight="#264F78",
    highlight_text="#FFFFFF",
    fixed_bg="#1A2A3A",
    fixed_text="#9CDCFE",
    pencil_text="#666666",
    conflict_bg="#5A1A1A",
    peer_bg="#1F2D3D",
    border="#777777",
    thin_border="#444444",
    black_cell_bg="#0d0d0d",
    cage_member_bg="#1e3a1e",
    cage_label_color="#88cc88",
    cage_dash_pattern=(4.0, 2.0),
)


def make_font(size_pt: int | None = None) -> QFont:
    """Return an Arial QFont, clamped to MIN_FONT_PT."""
    pt = max(MIN_FONT_PT, size_pt) if size_pt is not None else 11
    font = QFont(FONT_FAMILY, pt)
    return font


def apply_palette(app: QApplication, palette: Palette) -> None:
    """Push *palette* colours into the Qt application palette."""
    qp = QPalette()
    _set = qp.setColor

    _set(QPalette.ColorRole.Window,          QColor(palette.window_bg))
    _set(QPalette.ColorRole.WindowText,      QColor(palette.window_text))
    _set(QPalette.ColorRole.Base,            QColor(palette.base))
    _set(QPalette.ColorRole.AlternateBase,   QColor(palette.alt_base))
    _set(QPalette.ColorRole.Text,            QColor(palette.text))
    _set(QPalette.ColorRole.Button,          QColor(palette.button_bg))
    _set(QPalette.ColorRole.ButtonText,      QColor(palette.button_text))
    _set(QPalette.ColorRole.Highlight,       QColor(palette.highlight))
    _set(QPalette.ColorRole.HighlightedText, QColor(palette.highlight_text))

    app.setPalette(qp)
