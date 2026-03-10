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

from richards_sudoku.model.types import Board, Variant, VariantMetadata
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
        self.updateGeometry()  # K3: let QScrollArea re-evaluate size hints
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

    _PREFERRED_CELL_PX = 54   # preferred cell size in pixels
    _MIN_CELL_PX = 14          # minimum cell size for 25×25 scroll scenario

    def sizeHint(self) -> QSize:
        size = self._board.size if self._board is not None else 9
        px = size * self._PREFERRED_CELL_PX
        return QSize(px, px)

    def minimumSizeHint(self) -> QSize:
        size = self._board.size if self._board is not None else 9
        px = size * self._MIN_CELL_PX
        return QSize(px, px)

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

        # --- peer set and conflicts for selected cell ---
        peers: set[tuple[int, int]] = set()
        conflicts: set[tuple[int, int]] = set()
        sel = self._selected
        if sel and meta:
            if meta.name == Variant.KAKURO:
                # N4: peers are all cells in the same across/down run
                for run in (meta.constraints or {}).get("clues", []):
                    run_cells = [(int(p[0]), int(p[1])) for p in run["cells"]]
                    if sel in run_cells:
                        peers.update(rc for rc in run_cells if rc != sel)
            else:
                peers = _peer_cells(sel[0], sel[1], size, meta.region_layout, box_rows, box_cols)
            conflicts = _all_conflict_cells(board, size, meta.region_layout, meta)

        # --- cage membership set for Killer / KenKen ---
        cage_cells: set[tuple[int, int]] = set()
        cages: list[dict] = []
        if meta is not None:
            cages = meta.constraints.get("cages", []) or []
            if cages:
                for cage in cages:
                    for p in cage.get("cells", []):
                        cage_cells.add((int(p[0]), int(p[1])))

        # --- Codewords letter display (L3) ---
        # Build digit→letter inverse codebook when variant is Codewords.
        _inverse_codebook: dict[int, str] | None = None
        if meta is not None and meta.name.value == "codewords":
            codebook: dict[str, int] = meta.constraints.get("codebook") or {}
            if codebook:
                _inverse_codebook = {v: k for k, v in codebook.items()}
        for r in range(size):
            for c in range(size):
                rect = self._cell_rect(r, c, cell_size)
                cell = board.cell(r, c)

                # Background priority: selected > conflict > peer > cage_member > fixed > is_black > base
                if sel == (r, c):
                    bg = QColor(pal.highlight)
                elif (r, c) in conflicts:
                    bg = QColor(pal.conflict_bg)
                elif (r, c) in peers:
                    # Str8ts: black cells in selected row/col also get peer_bg
                    bg = QColor(pal.peer_bg)
                elif (r, c) in cage_cells:
                    bg = QColor(pal.cage_member_bg)
                elif cell.is_fixed:
                    bg = QColor(pal.fixed_bg)
                elif cell.is_black:
                    bg = QColor(pal.black_cell_bg)
                else:
                    bg = QColor(pal.base)
                painter.fillRect(rect, bg)

                # Value or candidates (skip rendering content for black cells)
                if cell.is_black:
                    continue
                if cell.value is not None:
                    display_sym = (
                        _inverse_codebook[cell.value]
                        if _inverse_codebook and cell.value in _inverse_codebook
                        else str(cell.value)
                    )
                    self._draw_value(painter, rect, display_sym, cell.is_fixed, sel == (r, c), pal)
                elif cell.candidates:
                    cand_offset = round(cell_size * 0.25) if (r, c) in cage_cells else 0
                    self._draw_candidates(painter, rect, cell.candidates, size, pal, cand_offset, _inverse_codebook)

        # --- draw cage labels for Killer / KenKen ---
        if cages:
            self._draw_cage_labels(painter, cages, size, cell_size, pal)

        # --- N3: draw diagonal clue labels on Kakuro black cells ---
        if meta is not None and meta.name == Variant.KAKURO:
            clue_positions = meta.constraints.get("clue_positions") or {}
            label_pt = max(4, round(cell_size * 0.17))
            painter.setFont(make_font(label_pt))
            pen = QPen(QColor(pal.cage_label_color))
            for key, clue_dict in clue_positions.items():
                # key may be a tuple (r, c) or a string "r,c" from JSON
                if isinstance(key, str):
                    kr, kc = (int(x) for x in key.split(","))
                else:
                    kr, kc = int(key[0]), int(key[1])
                rect = self._cell_rect(kr, kc, cell_size)
                # Diagonal divider
                painter.setPen(pen)
                painter.drawLine(rect.topLeft(), rect.bottomRight())
                # Upper-right half: down clue
                painter.setPen(QColor(pal.cage_label_color))
                if "down" in clue_dict:
                    tr_rect = QRect(
                        rect.x() + rect.width() // 2,
                        rect.y() + 1,
                        rect.width() // 2 - 1,
                        rect.height() // 2,
                    )
                    painter.drawText(
                        tr_rect,
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                        str(clue_dict["down"]),
                    )
                # Lower-left half: across clue
                if "across" in clue_dict:
                    bl_rect = QRect(
                        rect.x() + 1,
                        rect.y() + rect.height() // 2,
                        rect.width() // 2 - 1,
                        rect.height() // 2,
                    )
                    painter.drawText(
                        bl_rect,
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        str(clue_dict["across"]),
                    )

        # --- draw grid edges ---
        edge_dict = _build_edge_dict(meta, size, box_rows, box_cols)
        dash_thin = meta is not None and meta.name in (Variant.KILLER, Variant.KENKEN)
        _draw_edges(painter, size, cell_size, edge_dict, pal, dash_thin)

    def _draw_value(
        self,
        painter: QPainter,
        rect: QRect,
        value: int | str,
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
        offset_y: int = 0,
        inverse_codebook: dict[int, str] | None = None,
    ) -> None:
        # Mini-grid: fit candidates in a sqrt(size) × sqrt(size) sub-grid
        box_r, box_c = _box_dims(board_size)
        mini_w = rect.width() / box_c
        mini_h = (rect.height() - offset_y) / box_r
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
                rect.y() + offset_y + round(mr * mini_h),
                round(mini_w),
                round(mini_h),
            )
            painter.drawText(mini_rect, Qt.AlignmentFlag.AlignCenter,
                             inverse_codebook[sym] if inverse_codebook and sym in inverse_codebook else str(sym))

    def _draw_cage_labels(
        self,
        painter: QPainter,
        cages: list[dict],
        size: int,
        cell_size: float,
        pal: Palette,
    ) -> None:
        """Draw cage sum labels at the top-left (row-major minimum) cell of each cage."""
        label_pt = max(4, round(cell_size * 0.18))
        font = make_font(label_pt)
        painter.setFont(font)
        painter.setPen(QColor(pal.cage_label_color))
        for cage in cages:
            cells = [(int(p[0]), int(p[1])) for p in cage.get("cells", [])]
            if not cells:
                continue
            min_cell = min(cells, key=lambda rc: rc[0] * size + rc[1])
            r, c = min_cell
            rect = self._cell_rect(r, c, cell_size)
            label_rect = QRect(
                rect.x() + 1,
                rect.y() + 1,
                rect.width() // 2,
                rect.height() // 3,
            )
            # KenKen: show "12+", "6×", "2÷", "3−"; Killer: show sum only
            if "op" in cage and "target" in cage:
                _OP_DISPLAY = {"+": "+", "-": "\u2212", "*": "\u00d7", "/": "\u00f7"}
                label_text = f"{cage['target']}{_OP_DISPLAY.get(cage['op'], cage['op'])}"
            else:
                label_text = str(cage.get("sum", ""))
            painter.drawText(
                label_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                label_text,
            )

    def _draw_lines(
        self,
        painter: QPainter,
        size: int,
        cell_size: float,
        box_rows: int,
        box_cols: int,
        pal: Palette,
        region_layout: list[list[int]] | None = None,
    ) -> None:
        total = round(size * cell_size)

        thin_pen = QPen(QColor(pal.thin_border), 1)
        thick_pen = QPen(QColor(pal.border), 3)

        if region_layout is not None:
            # Jigsaw: draw each edge segment thick when it borders two different regions
            # (or is the outer grid boundary), thin otherwise.
            for i in range(size + 1):
                y = round(i * cell_size)
                x = round(i * cell_size)
                for j in range(size):
                    x0 = round(j * cell_size)
                    x1 = round((j + 1) * cell_size)
                    y0 = round(j * cell_size)
                    y1 = round((j + 1) * cell_size)

                    # Horizontal segment at row-line i, column j
                    # separates cell (i-1, j) above from cell (i, j) below
                    is_thick_h = (
                        i == 0 or i == size
                        or region_layout[i - 1][j] != region_layout[i][j]
                    )
                    painter.setPen(thick_pen if is_thick_h else thin_pen)
                    painter.drawLine(x0, y, x1, y)

                    # Vertical segment at col-line i, row j
                    # separates cell (j, i-1) left from cell (j, i) right
                    is_thick_v = (
                        i == 0 or i == size
                        or region_layout[j][i - 1] != region_layout[j][i]
                    )
                    painter.setPen(thick_pen if is_thick_v else thin_pen)
                    painter.drawLine(x, y0, x, y1)
        else:
            # Standard: thick lines at regular box-boundary intervals
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
            # G5: don't select black cells on click
            if not self._board.cell(row, col).is_black:
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
            self._move_selection(dr, dc)
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
            # G5: no digit input/pencil on black cells
            if cell.is_fixed or cell.is_black:
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

    def _move_selection(self, dr: int, dc: int) -> None:
        """Move the selection by (dr, dc), clamping to [0, size-1], skipping black cells."""
        if self._board is None:
            return
        size = self._board.size
        if self._selected:
            r, c = self._selected
        else:
            r, c = 0, 0
        nr = max(0, min(size - 1, r + dr))
        nc = max(0, min(size - 1, c + dc))
        # Skip black cells by continuing in the same direction
        for _ in range(size):
            cell = self._board.cell(nr, nc)
            if not cell.is_black:
                break
            nr = max(0, min(size - 1, nr + dr))
            nc = max(0, min(size - 1, nc + dc))
        self._selected = (nr, nc)
        self.cell_selected.emit(nr, nc)
        self.update()

    def _advance_selection(self, delta: int, skip_black: bool = True) -> None:
        if self._board is None:
            return
        size = self._board.size
        total = size * size
        if self._selected:
            r, c = self._selected
            idx = r * size + c
        else:
            idx = -delta
        for _ in range(total):
            idx = (idx + delta) % total
            nr, nc = idx // size, idx % size
            if not skip_black or not self._board.cell(nr, nc).is_black:
                break
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


def _all_conflict_cells(
    board: Board,
    size: int,
    region_layout: list[list[int]],
    meta: "VariantMetadata | None" = None,
) -> set[tuple[int, int]]:
    """Return ALL cells that participate in any conflict on the board.

    A conflict exists when two cells in the same row, column, or region
    share the same non-None value.  Both cells are included in the result.
    Also adds variant-specific conflict detection for Str8ts (G8a) and
    Killer (G8b).
    """
    box_rows, box_cols = _box_dims(size)
    conflicts: set[tuple[int, int]] = set()

    # Build units: rows, cols, regions
    row_units = [[(r, c) for c in range(size)] for r in range(size)]
    col_units = [[(r, c) for r in range(size)] for c in range(size)]
    num_regions = max(region_layout[r][c] for r in range(size) for c in range(size)) + 1
    region_units: list[list[tuple[int, int]]] = [[] for _ in range(num_regions)]
    for r in range(size):
        for c in range(size):
            region_units[region_layout[r][c]].append((r, c))

    for unit in row_units + col_units + [reg for reg in region_units if reg]:
        val_cells: dict[int, list[tuple[int, int]]] = {}
        for r, c in unit:
            v = board.cell(r, c).value
            if v is not None:
                val_cells.setdefault(v, []).append((r, c))
        for v, cells in val_cells.items():
            if len(cells) > 1:
                for cell in cells:
                    conflicts.add(cell)

    # G8a — Str8ts straight-invalidity detection
    if meta is not None and meta.name == Variant.STR8TS:
        black_set: set[tuple[int, int]] = {
            (int(p[0]), int(p[1]))
            for p in (meta.constraints.get("black_cells") or [])
        }

        def _check_run(run_cells: list[tuple[int, int]]) -> None:
            if len(run_cells) < 2:
                return
            placed = [
                (r, c, board.cell(r, c).value)
                for r, c in run_cells
                if board.cell(r, c).value is not None
            ]
            if len(placed) < 2:
                return
            vals = [v for _, _, v in placed]
            if max(vals) - min(vals) >= len(run_cells):
                for r, c, _ in placed:
                    conflicts.add((r, c))

        for row in range(size):
            run: list[tuple[int, int]] = []
            for col in range(size):
                if (row, col) in black_set:
                    _check_run(run)
                    run = []
                else:
                    run.append((row, col))
            _check_run(run)

        for col in range(size):
            run = []
            for row in range(size):
                if (row, col) in black_set:
                    _check_run(run)
                    run = []
                else:
                    run.append((row, col))
            _check_run(run)

    # G8b — Killer cage-excess detection
    elif meta is not None and meta.name == Variant.KILLER:
        for cage in (meta.constraints.get("cages") or []):
            target = cage.get("sum", 0)
            cage_coords = [(int(p[0]), int(p[1])) for p in cage.get("cells", [])]
            placed_vals = [
                board.cell(r, c).value
                for r, c in cage_coords
                if board.cell(r, c).value is not None
            ]
            if placed_vals and sum(placed_vals) > target:
                for r, c in cage_coords:
                    if board.cell(r, c).value is not None:
                        conflicts.add((r, c))

    return conflicts


def _build_edge_dict(
    meta: "VariantMetadata | None",
    size: int,
    box_rows: int,
    box_cols: int,
) -> dict[tuple[int, int, str], bool]:
    """Build edge-thickness dict for *meta*.

    Key ``(r, c, "H")`` = horizontal edge **above** row *r* at column *c*
    (r in 0..size inclusive).
    Key ``(r, c, "V")`` = vertical edge **left of** col *c* at row *r*
    (c in 0..size inclusive).
    Value: ``True`` = thick border; ``False`` = thin border.
    """
    edges: dict[tuple[int, int, str], bool] = {}
    variant = meta.name if meta is not None else None

    if meta is not None and variant == Variant.JIGSAW:
        layout = meta.region_layout
        for r in range(size + 1):
            for c in range(size):
                thick = r == 0 or r == size or layout[r - 1][c] != layout[r][c]
                edges[(r, c, "H")] = thick
        for r in range(size):
            for c in range(size + 1):
                thick = c == 0 or c == size or layout[r][c - 1] != layout[r][c]
                edges[(r, c, "V")] = thick

    elif meta is not None and variant in (Variant.KILLER, Variant.KENKEN):
        cages = meta.constraints.get("cages", []) or []
        cell_cage: dict[tuple[int, int], int] = {}
        for cage_idx, cage in enumerate(cages):
            for cell in cage.get("cells", []):
                cell_cage[(int(cell[0]), int(cell[1]))] = cage_idx
        for r in range(size + 1):
            for c in range(size):
                if r == 0 or r == size:
                    thick = True
                else:
                    thick = cell_cage.get((r - 1, c), -1) != cell_cage.get((r, c), -2)
                edges[(r, c, "H")] = thick
        for r in range(size):
            for c in range(size + 1):
                if c == 0 or c == size:
                    thick = True
                else:
                    thick = cell_cage.get((r, c - 1), -1) != cell_cage.get((r, c), -2)
                edges[(r, c, "V")] = thick

    else:
        # Standard / Str8ts: regular box-boundary thick lines
        for r in range(size + 1):
            for c in range(size):
                edges[(r, c, "H")] = r % box_rows == 0
        for r in range(size):
            for c in range(size + 1):
                edges[(r, c, "V")] = c % box_cols == 0

    return edges


def _draw_edges(
    painter: QPainter,
    size: int,
    cell_size: float,
    edge_dict: dict[tuple[int, int, str], bool],
    pal: Palette,
    dash_thin: bool = False,
) -> None:
    """Render all grid edges from *edge_dict* using *pal* colours.

    When *dash_thin* is True, thin (intra-cage) edges use
    ``pal.cage_dash_pattern`` for a dashed appearance (Killer variant).
    """
    thin_pen = QPen(QColor(pal.thin_border), 1)
    thick_pen = QPen(QColor(pal.border), 3)

    if dash_thin:
        dash_pen = QPen(QColor(pal.thin_border), 1)
        dash_pen.setStyle(Qt.PenStyle.CustomDashLine)
        dash_pen.setDashPattern(list(pal.cage_dash_pattern))
    else:
        dash_pen = thin_pen

    # Horizontal edges (above row r, spanning column c to c+1)
    for r in range(size + 1):
        for c in range(size):
            thick = edge_dict.get((r, c, "H"), r == 0 or r == size)
            x0 = round(c * cell_size)
            x1 = round((c + 1) * cell_size)
            y = round(r * cell_size)
            painter.setPen(thick_pen if thick else dash_pen)
            painter.drawLine(x0, y, x1, y)

    # Vertical edges (left of col c, spanning row r to r+1)
    for r in range(size):
        for c in range(size + 1):
            thick = edge_dict.get((r, c, "V"), c == 0 or c == size)
            x = round(c * cell_size)
            y0 = round(r * cell_size)
            y1 = round((r + 1) * cell_size)
            painter.setPen(thick_pen if thick else dash_pen)
            painter.drawLine(x, y0, x, y1)
