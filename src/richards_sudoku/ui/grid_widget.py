"""SudokuGridWidget — a custom QWidget that renders a Sudoku board.

Responsibilities
----------------
* Paint the board: cells, thick box borders, thin cell borders.
* Highlight the selected cell, its peers, and conflicts.
* Show pencil/candidate marks in a 3×3 mini-grid inside each cell.
* Accept keyboard navigation (arrow keys, digit keys, Delete/Backspace).
* Accept mouse click selection.
* Emit signals for user edits (value entered, candidate toggled).

The widget is intentionally data-only: it holds a reference to a Board
and a VariantMetadata, but never modifies them directly.  All mutations
go through signals so the controller layer can apply, record, and undo.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PyQt6.QtCore import (
    QRect,
    QSize,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import QSizePolicy, QWidget

from richards_sudoku.model.types import Board, VariantMetadata
from richards_sudoku.ui.theme import DARK, LIGHT, MIN_FONT_PT, Palette, make_font

if TYPE_CHECKING:
    pass


class SudokuGridWidget(QWidget):
    """Visual Sudoku board.

    Signals
    -------
    cell_selected(row, col)
        Emitted when the user selects a different cell.
    value_entered(row, col, value)
        Emitted when the user types a digit (1-9) into the selected cell.
        value=0 means the user pressed Delete/Backspace (clear cell).
    pencil_toggled(row, col, value)
        Emitted when the user toggles a candidate in pencil mode.
    """

    cell_selected = pyqtSignal(int, int)
    value_entered = pyqtSignal(int, int, int)
    pencil_toggled = pyqtSignal(int, int, int)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._board: Board | None = None
        self._meta: VariantMetadata | None = None
        self._selected: tuple[int, int] | None = None
        self._pencil_mode: bool = False
        self._dark_mode: bool = False
        self._palette: Palette = LIGHT

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # ------------------------------------------------------------------
    # Data binding
    # ------------------------------------------------------------------

    def set_board(self, board: Board, meta: VariantMetadata) -> None:
        """Bind a new board+meta and repaint."""
        self._board = board
        self._meta = meta
        self._selected = None
        self.update()

    def refresh(self) -> None:
        """Request a repaint after external board mutation."""
        self.update()

    # ------------------------------------------------------------------
    # Mode toggles
    # ------------------------------------------------------------------

    def set_pencil_mode(self, enabled: bool) -> None:
        self._pencil_mode = enabled

    @property
    def pencil_mode(self) -> bool:
        return self._pencil_mode

    def set_dark_mode(self, dark: bool) -> None:
        self._dark_mode = dark
        self._palette = DARK if dark else LIGHT
        self.update()

    @property
    def selected_cell(self) -> tuple[int, int] | None:
        return self._selected

    def select_cell(self, row: int, col: int) -> None:
        """Programmatically select a cell."""
        if self._board is None:
            return
        size = self._board.size
        if 0 <= row < size and 0 <= col < size:
            self._selected = (row, col)
            self.cell_selected.emit(row, col)
            self.update()

    # ------------------------------------------------------------------
    # Size hints
    # ------------------------------------------------------------------

    def sizeHint(self) -> QSize:
        return QSize(540, 540)

    def minimumSizeHint(self) -> QSize:
        return QSize(270, 270)

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:  # noqa: N802
        if self._board is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self._draw_board(painter)
        painter.end()

    def _cell_rect(self, row: int, col: int, cell_size: float) -> QRect:
        x = round(col * cell_size)
        y = round(row * cell_size)
        w = round((col + 1) * cell_size) - x
        h = round((row + 1) * cell_size) - y
        return QRect(x, y, w, h)

    def _draw_board(self, painter: QPainter) -> None:
        board = self._board
        meta = self._meta
        size = board.size
        pal = self._palette

        side = min(self.width(), self.height())
        cell_size = side / size

        # Compute box dimensions (sqrt for standard; 1×size otherwise)
        box_rows, box_cols = _box_dims(size)

        # --- peer set for selected cell ---
        peers: set[tuple[int, int]] = set()
        conflicts: set[tuple[int, int]] = set()
        sel = self._selected
        if sel and meta:
            peers = _peer_cells(sel[0], sel[1], size, meta.region_layout, box_rows, box_cols)
            conflicts = _conflict_cells(board, sel[0], sel[1], size, meta.region_layout, box_rows, box_cols)

        # --- draw cells ---
        for r in range(size):
            for c in range(size):
                rect = self._cell_rect(r, c, cell_size)
                cell = board.cell(r, c)

                # Background
                if sel == (r, c):
                    bg = QColor(pal.highlight)
                elif (r, c) in conflicts:
                    bg = QColor(pal.conflict_bg)
                elif (r, c) in peers:
                    bg = QColor(pal.peer_bg)
                elif cell.is_fixed:
                    bg = QColor(pal.fixed_bg)
                else:
                    bg = QColor(pal.base)
                painter.fillRect(rect, bg)

                # Value or candidates
                if cell.value is not None:
                    self._draw_value(painter, rect, cell.value, cell.is_fixed, sel == (r, c), pal)
                elif cell.candidates:
                    self._draw_candidates(painter, rect, cell.candidates, size, pal)

        # --- draw grid lines ---
        self._draw_lines(painter, size, cell_size, box_rows, box_cols, pal)

    def _draw_value(
        self,
        painter: QPainter,
        rect: QRect,
        value: int,
        is_fixed: bool,
        is_selected: bool,
        pal: Palette,
    ) -> None:
        cell_pt = max(MIN_FONT_PT, round(rect.height() * 0.55))
        font = make_font(cell_pt)
        font.setBold(is_fixed)
        painter.setFont(font)
        if is_selected:
            color = QColor(pal.highlight_text)
        elif is_fixed:
            color = QColor(pal.fixed_text)
        else:
            color = QColor(pal.text)
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(value))

    def _draw_candidates(
        self,
        painter: QPainter,
        rect: QRect,
        candidates: set[int],
        board_size: int,
        pal: Palette,
    ) -> None:
        # Mini-grid: fit candidates in a sqrt(size) × sqrt(size) sub-grid
        box_r, box_c = _box_dims(board_size)
        mini_w = rect.width() / box_c
        mini_h = rect.height() / box_r
        cand_pt = max(MIN_FONT_PT, round(mini_h * 0.6))
        font = make_font(cand_pt)
        painter.setFont(font)
        painter.setPen(QColor(pal.pencil_text))

        symbols = list(range(1, board_size + 1))
        for idx, sym in enumerate(symbols):
            if sym not in candidates:
                continue
            mr = idx // box_c
            mc = idx % box_c
            mini_rect = QRect(
                rect.x() + round(mc * mini_w),
                rect.y() + round(mr * mini_h),
                round(mini_w),
                round(mini_h),
            )
            painter.drawText(mini_rect, Qt.AlignmentFlag.AlignCenter, str(sym))

    def _draw_lines(
        self,
        painter: QPainter,
        size: int,
        cell_size: float,
        box_rows: int,
        box_cols: int,
        pal: Palette,
    ) -> None:
        total = round(size * cell_size)

        thin_pen = QPen(QColor(pal.thin_border), 1)
        thick_pen = QPen(QColor(pal.border), 3)

        for i in range(size + 1):
            is_box_h = (i % box_rows == 0)
            is_box_v = (i % box_cols == 0)
            y = round(i * cell_size)
            x = round(i * cell_size)

            # horizontal
            painter.setPen(thick_pen if is_box_h else thin_pen)
            painter.drawLine(0, y, total, y)

            # vertical
            painter.setPen(thick_pen if is_box_v else thin_pen)
            painter.drawLine(x, 0, x, total)

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._board is None:
            return
        size = self._board.size
        side = min(self.width(), self.height())
        cell_size = side / size
        col = int(event.position().x() / cell_size)
        row = int(event.position().y() / cell_size)
        if 0 <= row < size and 0 <= col < size:
            self._selected = (row, col)
            self.cell_selected.emit(row, col)
            self.update()
        self.setFocus()

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if self._board is None:
            super().keyPressEvent(event)
            return

        key = event.key()
        size = self._board.size

        # --- Navigation ---
        nav = {
            Qt.Key.Key_Up:    (-1,  0),
            Qt.Key.Key_Down:  ( 1,  0),
            Qt.Key.Key_Left:  ( 0, -1),
            Qt.Key.Key_Right: ( 0,  1),
        }
        if key in nav:
            dr, dc = nav[key]
            if self._selected:
                r, c = self._selected
                nr = (r + dr) % size
                nc = (c + dc) % size
            else:
                nr, nc = 0, 0
            self._selected = (nr, nc)
            self.cell_selected.emit(nr, nc)
            self.update()
            return

        # --- Tab / Shift-Tab ---
        if key == Qt.Key.Key_Tab:
            self._advance_selection(1)
            return
        if key == Qt.Key.Key_Backtab:
            self._advance_selection(-1)
            return

        # --- Digit entry ---
        if self._selected:
            row, col = self._selected
            cell = self._board.cell(row, col)
            if cell.is_fixed:
                super().keyPressEvent(event)
                return

            digit: int | None = None
            if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
                digit = key - Qt.Key.Key_0

            if digit is not None and digit <= size:
                if self._pencil_mode:
                    self.pencil_toggled.emit(row, col, digit)
                else:
                    self.value_entered.emit(row, col, digit)
                return

            if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace, Qt.Key.Key_0):
                self.value_entered.emit(row, col, 0)
                return

        super().keyPressEvent(event)

    def _advance_selection(self, delta: int) -> None:
        if self._board is None:
            return
        size = self._board.size
        total = size * size
        if self._selected:
            r, c = self._selected
            idx = r * size + c
        else:
            idx = -delta
        idx = (idx + delta) % total
        self._selected = (idx // size, idx % size)
        self.cell_selected.emit(self._selected[0], self._selected[1])
        self.update()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _box_dims(size: int) -> tuple[int, int]:
    """Return (box_rows, box_cols) for a board of *size*."""
    sq = int(math.isqrt(size))
    if sq * sq == size:
        return sq, sq
    # Non-square: treat as 1 big region
    return 1, size


def _peer_cells(
    row: int,
    col: int,
    size: int,
    region_layout: list[list[int]],
    box_rows: int,
    box_cols: int,
) -> set[tuple[int, int]]:
    """Return all cells in the same row, column, or region as (row, col)."""
    peers: set[tuple[int, int]] = set()
    region = region_layout[row][col]
    for r in range(size):
        for c in range(size):
            if (r, c) != (row, col):
                if r == row or c == col or region_layout[r][c] == region:
                    peers.add((r, c))
    return peers


def _conflict_cells(
    board: Board,
    row: int,
    col: int,
    size: int,
    region_layout: list[list[int]],
    box_rows: int,
    box_cols: int,
) -> set[tuple[int, int]]:
    """Return peers whose value equals the selected cell's value (conflict)."""
    val = board.cell(row, col).value
    if val is None:
        return set()
    peers = _peer_cells(row, col, size, region_layout, box_rows, box_cols)
    return {(r, c) for (r, c) in peers if board.cell(r, c).value == val}
