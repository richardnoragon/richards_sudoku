"""pytest-qt smoke tests for the UI shell.

Covers:
- MainWindow instantiates without error
- SudokuGridWidget renders with a board
- Cell selection via mouse simulation
- Arrow-key navigation
- Digit key fires value_entered signal
- Delete key fires value_entered(0) signal
- Pencil mode toggle
- Pencil mode fires pencil_toggled signal
- Tab / Shift-Tab advance selection
- Dark mode toggle
- All expected actions exist on MainWindow
- Status bar labels present
"""
from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from richards_sudoku.main import MainWindow
from richards_sudoku.model.types import Board, Variant, VariantMetadata
from richards_sudoku.ui.grid_widget import SudokuGridWidget
from richards_sudoku.ui.theme import DARK, LIGHT, apply_palette, make_font


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def meta() -> VariantMetadata:
    return VariantMetadata.standard_9x9()


@pytest.fixture()
def board() -> Board:
    b = Board(size=9, variant=Variant.STANDARD)
    b.cell(0, 0).value = 5
    b.cell(0, 0).is_fixed = True
    b.cell(1, 1).value = 3
    b.cell(4, 4).candidates = {1, 2, 7}
    return b


@pytest.fixture()
def main_window(qtbot: QtBot) -> MainWindow:
    win = MainWindow()
    qtbot.addWidget(win)
    return win


@pytest.fixture()
def grid_widget(qtbot: QtBot, board: Board, meta: VariantMetadata) -> SudokuGridWidget:
    w = SudokuGridWidget()
    w.set_board(board, meta)
    w.resize(540, 540)
    qtbot.addWidget(w)
    return w


# ---------------------------------------------------------------------------
# MainWindow smoke
# ---------------------------------------------------------------------------

class TestMainWindowSmoke:

    def test_window_title(self, main_window: MainWindow):
        assert "Sudoku" in main_window.windowTitle()

    def test_has_menu_bar(self, main_window: MainWindow):
        assert main_window.menuBar() is not None

    def test_has_status_bar(self, main_window: MainWindow):
        assert main_window.statusBar() is not None

    def test_central_widget_is_scroll_area_wrapping_grid(self, main_window: MainWindow):
        from PyQt6.QtWidgets import QScrollArea
        scroll = main_window.centralWidget()
        assert isinstance(scroll, QScrollArea)
        assert isinstance(scroll.widget(), SudokuGridWidget)

    def test_file_menu_exists(self, main_window: MainWindow):
        titles = [a.text() for a in main_window.menuBar().actions()]
        assert any("File" in t for t in titles)

    def test_edit_menu_exists(self, main_window: MainWindow):
        titles = [a.text() for a in main_window.menuBar().actions()]
        assert any("Edit" in t for t in titles)

    def test_game_menu_exists(self, main_window: MainWindow):
        titles = [a.text() for a in main_window.menuBar().actions()]
        assert any("Game" in t for t in titles)

    def test_view_menu_exists(self, main_window: MainWindow):
        titles = [a.text() for a in main_window.menuBar().actions()]
        assert any("View" in t for t in titles)

    def test_expected_actions_exist(self, main_window: MainWindow):
        action_texts = {a.text() for a in main_window.findChildren(type(main_window._act_new))}
        # Check key action labels are present
        for label in ("&New Game", "&Open…", "&Save", "&Undo", "&Redo",
                      "&Pencil Mode", "&Hint", "&Dark Mode"):
            assert label in action_texts, f"Missing action: {label}"

    def test_timer_label_present(self, main_window: MainWindow):
        assert main_window._lbl_timer is not None
        assert ":" in main_window._lbl_timer.text()

    def test_mode_label_present(self, main_window: MainWindow):
        assert "Normal" in main_window._lbl_mode.text()


# ---------------------------------------------------------------------------
# SudokuGridWidget — render & selection
# ---------------------------------------------------------------------------

class TestGridWidgetRender:

    def test_set_board_does_not_raise(self, grid_widget: SudokuGridWidget):
        # Just verifying no exception during set_board
        assert grid_widget._board is not None

    def test_initial_selection_is_none(self, grid_widget: SudokuGridWidget):
        assert grid_widget.selected_cell is None

    def test_select_cell_programmatic(self, grid_widget: SudokuGridWidget):
        grid_widget.select_cell(3, 4)
        assert grid_widget.selected_cell == (3, 4)

    def test_select_cell_emits_signal(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        with qtbot.waitSignal(grid_widget.cell_selected, timeout=500) as sig:
            grid_widget.select_cell(2, 2)
        assert sig.args == [2, 2]

    def test_select_out_of_bounds_ignored(self, grid_widget: SudokuGridWidget):
        grid_widget.select_cell(0, 0)
        grid_widget.select_cell(99, 99)
        # Should still be at (0,0)
        assert grid_widget.selected_cell == (0, 0)

    def test_paintEvent_does_not_raise(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.show()
        qtbot.waitExposed(grid_widget)
        grid_widget.update()
        # If we get here without exception, paint succeeded

    def test_refresh_triggers_repaint(self, grid_widget: SudokuGridWidget):
        # Smoke: refresh() should not raise
        grid_widget.refresh()


# ---------------------------------------------------------------------------
# Keyboard navigation
# ---------------------------------------------------------------------------

class TestKeyboardNavigation:

    def test_arrow_down_moves_selection(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.select_cell(0, 0)
        qtbot.keyClick(grid_widget, Qt.Key.Key_Down)
        assert grid_widget.selected_cell == (1, 0)

    def test_arrow_right_moves_selection(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.select_cell(0, 0)
        qtbot.keyClick(grid_widget, Qt.Key.Key_Right)
        assert grid_widget.selected_cell == (0, 1)

    def test_arrow_up_clamps(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        # Arrow keys clamp at the board edge (no wrap-around)
        grid_widget.select_cell(0, 0)
        qtbot.keyClick(grid_widget, Qt.Key.Key_Up)
        assert grid_widget.selected_cell == (0, 0)

    def test_arrow_left_clamps(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        # Arrow keys clamp at the board edge (no wrap-around)
        grid_widget.select_cell(0, 0)
        qtbot.keyClick(grid_widget, Qt.Key.Key_Left)
        assert grid_widget.selected_cell == (0, 0)

    def test_tab_advances_selection(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.select_cell(0, 0)
        qtbot.keyClick(grid_widget, Qt.Key.Key_Tab)
        assert grid_widget.selected_cell == (0, 1)

    def test_tab_wraps_at_end(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.select_cell(8, 8)
        qtbot.keyClick(grid_widget, Qt.Key.Key_Tab)
        assert grid_widget.selected_cell == (0, 0)

    def test_shift_tab_goes_back(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.select_cell(0, 1)
        qtbot.keyClick(grid_widget, Qt.Key.Key_Backtab)
        assert grid_widget.selected_cell == (0, 0)


# ---------------------------------------------------------------------------
# Digit / delete signals
# ---------------------------------------------------------------------------

class TestGridSignals:

    def test_digit_key_emits_value_entered(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        # Select a non-fixed cell
        grid_widget.select_cell(2, 2)
        with qtbot.waitSignal(grid_widget.value_entered, timeout=500) as sig:
            qtbot.keyClick(grid_widget, Qt.Key.Key_7)
        assert sig.args == [2, 2, 7]

    def test_digit_key_on_fixed_cell_does_not_emit(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        # (0,0) is fixed in our fixture
        grid_widget.select_cell(0, 0)
        with qtbot.assertNotEmitted(grid_widget.value_entered):
            qtbot.keyClick(grid_widget, Qt.Key.Key_5)

    def test_delete_emits_value_zero(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.select_cell(2, 2)
        with qtbot.waitSignal(grid_widget.value_entered, timeout=500) as sig:
            qtbot.keyClick(grid_widget, Qt.Key.Key_Delete)
        assert sig.args == [2, 2, 0]

    def test_backspace_emits_value_zero(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.select_cell(2, 2)
        with qtbot.waitSignal(grid_widget.value_entered, timeout=500) as sig:
            qtbot.keyClick(grid_widget, Qt.Key.Key_Backspace)
        assert sig.args == [2, 2, 0]

    def test_pencil_mode_emits_pencil_toggled(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.set_pencil_mode(True)
        grid_widget.select_cell(2, 2)
        with qtbot.waitSignal(grid_widget.pencil_toggled, timeout=500) as sig:
            qtbot.keyClick(grid_widget, Qt.Key.Key_3)
        assert sig.args == [2, 2, 3]

    def test_pencil_mode_does_not_emit_value_entered(self, qtbot: QtBot, grid_widget: SudokuGridWidget):
        grid_widget.set_pencil_mode(True)
        grid_widget.select_cell(2, 2)
        with qtbot.assertNotEmitted(grid_widget.value_entered):
            qtbot.keyClick(grid_widget, Qt.Key.Key_3)


# ---------------------------------------------------------------------------
# Pencil mode toggle
# ---------------------------------------------------------------------------

class TestPencilMode:

    def test_default_not_pencil(self, grid_widget: SudokuGridWidget):
        assert not grid_widget.pencil_mode

    def test_set_pencil_mode_true(self, grid_widget: SudokuGridWidget):
        grid_widget.set_pencil_mode(True)
        assert grid_widget.pencil_mode

    def test_set_pencil_mode_false(self, grid_widget: SudokuGridWidget):
        grid_widget.set_pencil_mode(True)
        grid_widget.set_pencil_mode(False)
        assert not grid_widget.pencil_mode

    def test_main_window_pencil_action_toggles_grid(self, main_window: MainWindow):
        main_window._act_pencil.setChecked(True)
        main_window._act_pencil.triggered.emit(True)
        grid = main_window._grid
        assert grid.pencil_mode is True

        main_window._act_pencil.setChecked(False)
        main_window._act_pencil.triggered.emit(False)
        assert grid.pencil_mode is False


# ---------------------------------------------------------------------------
# Dark mode toggle
# ---------------------------------------------------------------------------

class TestDarkMode:

    def test_set_dark_mode_updates_palette(self, grid_widget: SudokuGridWidget):
        grid_widget.set_dark_mode(True)
        assert grid_widget._palette is DARK
        grid_widget.set_dark_mode(False)
        assert grid_widget._palette is LIGHT

    def test_main_window_dark_action_works(self, main_window: MainWindow):
        main_window._act_dark.setChecked(True)
        main_window._act_dark.triggered.emit(True)
        assert main_window._dark_mode is True

        main_window._act_dark.setChecked(False)
        main_window._act_dark.triggered.emit(False)
        assert main_window._dark_mode is False


# ---------------------------------------------------------------------------
# Theme / font helpers
# ---------------------------------------------------------------------------

class TestTheme:

    def test_make_font_family(self):
        f = make_font(11)
        assert f.family() == "Arial"

    def test_make_font_min_clamp(self):
        f = make_font(2)
        assert f.pointSize() >= 6

    def test_dark_palette_has_all_fields(self):
        for field_name in DARK.__dataclass_fields__:
            assert getattr(DARK, field_name) is not None

    def test_light_palette_has_all_fields(self):
        for field_name in LIGHT.__dataclass_fields__:
            assert getattr(LIGHT, field_name) is not None


# ---------------------------------------------------------------------------
# T6: Variant smoke — render each variant board without crashing
# ---------------------------------------------------------------------------

def _standard_layout() -> list[list[int]]:
    return [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]


def _jigsaw_meta() -> VariantMetadata:
    return VariantMetadata(
        name=Variant.JIGSAW,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=_standard_layout(),
        constraints={},
    )


def _str8ts_meta() -> VariantMetadata:
    return VariantMetadata(
        name=Variant.STR8TS,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=_standard_layout(),
        constraints={"black_cells": [[0, 4], [4, 0], [8, 8]], "black_givens": []},
    )


def _killer_meta() -> VariantMetadata:
    # 9 box-region cages, each 9 cells, sum = 45
    cages = []
    for box_r in range(3):
        for box_c in range(3):
            cells = [[box_r * 3 + dr, box_c * 3 + dc] for dr in range(3) for dc in range(3)]
            cages.append({"cells": cells, "sum": 45})
    return VariantMetadata(
        name=Variant.KILLER,
        size=9,
        symbols=list(range(1, 10)),
        region_layout=_standard_layout(),
        constraints={"cages": cages},
    )


class TestVariantSmoke:
    """T6: grid_widget renders each variant without crashing."""

    def test_jigsaw_render(self, qtbot: QtBot):
        meta = _jigsaw_meta()
        board = Board(size=9, variant=Variant.JIGSAW)
        w = SudokuGridWidget()
        w.set_board(board, meta)
        w.resize(540, 540)
        qtbot.addWidget(w)
        w.show()
        qtbot.waitExposed(w)
        w.update()

    def test_str8ts_render_with_black_cells(self, qtbot: QtBot):
        meta = _str8ts_meta()
        board = Board(size=9, variant=Variant.STR8TS)
        # Mark black cells on the board
        for pos in meta.constraints.get("black_cells", []):
            board.cell(int(pos[0]), int(pos[1])).is_black = True
        w = SudokuGridWidget()
        w.set_board(board, meta)
        w.resize(540, 540)
        qtbot.addWidget(w)
        w.show()
        qtbot.waitExposed(w)
        w.update()

    def test_killer_render_with_cage_overlay(self, qtbot: QtBot):
        meta = _killer_meta()
        board = Board(size=9, variant=Variant.KILLER)
        w = SudokuGridWidget()
        w.set_board(board, meta)
        w.resize(540, 540)
        qtbot.addWidget(w)
        w.show()
        qtbot.waitExposed(w)
        w.update()

    def test_conflict_highlight_renders(self, qtbot: QtBot):
        """Board with a row-conflict renders without crashing."""
        meta = VariantMetadata.standard_9x9()
        board = Board(size=9, variant=Variant.STANDARD)
        board.cell(0, 0).value = 5
        board.cell(0, 1).value = 5  # conflict
        w = SudokuGridWidget()
        w.set_board(board, meta)
        w.resize(540, 540)
        qtbot.addWidget(w)
        w.show()
        qtbot.waitExposed(w)
        w.update()


# ---------------------------------------------------------------------------
# T6: Variant constraint invariants
# ---------------------------------------------------------------------------

class TestVariantConstraintInvariants:
    """Each variant's metadata satisfies its structural constraints."""

    def test_standard_has_nine_equal_regions(self):
        meta = VariantMetadata.standard_9x9()
        from collections import Counter
        counts = Counter(
            meta.region_layout[r][c] for r in range(9) for c in range(9)
        )
        assert len(counts) == 9
        assert all(v == 9 for v in counts.values())

    def test_jigsaw_has_nine_equal_regions(self):
        meta = _jigsaw_meta()
        from collections import Counter
        counts = Counter(
            meta.region_layout[r][c] for r in range(9) for c in range(9)
        )
        assert len(counts) == 9
        assert all(v == 9 for v in counts.values())

    def test_str8ts_black_cells_in_bounds(self):
        meta = _str8ts_meta()
        for pos in meta.constraints["black_cells"]:
            assert 0 <= int(pos[0]) < 9
            assert 0 <= int(pos[1]) < 9

    def test_killer_cages_cover_all_cells(self):
        meta = _killer_meta()
        covered = set()
        for cage in meta.constraints["cages"]:
            for pos in cage["cells"]:
                covered.add((int(pos[0]), int(pos[1])))
        assert len(covered) == 81

    def test_killer_cages_no_overlap(self):
        meta = _killer_meta()
        covered: list[tuple[int, int]] = []
        for cage in meta.constraints["cages"]:
            for pos in cage["cells"]:
                covered.append((int(pos[0]), int(pos[1])))
        assert len(covered) == len(set(covered))

    def test_killer_cage_sums_positive(self):
        meta = _killer_meta()
        for cage in meta.constraints["cages"]:
            assert cage["sum"] > 0


# ---------------------------------------------------------------------------
# T6: Text import/export round-trips per variant
# ---------------------------------------------------------------------------

class TestTextFormatRoundTrip:
    """import_text(export_text(…)) reconstructs the same values and metadata."""

    from richards_sudoku.services.text_format import export_text, import_text

    def _board_values(self, board: Board) -> list[list[int | None]]:
        return [
            [board.cell(r, c).value for c in range(9)]
            for r in range(9)
        ]

    def test_standard_round_trip(self):
        from richards_sudoku.services.text_format import export_text, import_text
        meta = VariantMetadata.standard_9x9()
        board = Board(size=9, variant=Variant.STANDARD)
        board.cell(0, 0).value = 3
        board.cell(4, 4).value = 7
        vals = self._board_values(board)
        text = export_text(vals, meta.to_dict(), seed=42, difficulty="medium")
        bv2, md2, seed2, diff2 = import_text(text)
        assert bv2[0][0] == 3
        assert bv2[4][4] == 7
        assert seed2 == 42
        assert diff2 == "medium"

    def test_jigsaw_round_trip_preserves_region_layout(self):
        from richards_sudoku.services.text_format import export_text, import_text
        meta = _jigsaw_meta()
        board = Board(size=9, variant=Variant.JIGSAW)
        board.cell(1, 1).value = 2
        vals = self._board_values(board)
        text = export_text(vals, meta.to_dict(), seed=7)
        bv2, md2, _, _ = import_text(text)
        assert bv2[1][1] == 2
        assert md2["region_layout"] == meta.region_layout

    def test_str8ts_round_trip_preserves_black_cells(self):
        from richards_sudoku.services.text_format import export_text, import_text
        meta = _str8ts_meta()
        board = Board(size=9, variant=Variant.STR8TS)
        board.cell(2, 2).value = 5
        vals = self._board_values(board)
        text = export_text(vals, meta.to_dict(), seed=0)
        bv2, md2, _, _ = import_text(text)
        assert bv2[2][2] == 5
        exported_blacks = {(int(p[0]), int(p[1])) for p in md2["constraints"]["black_cells"]}
        original_blacks = {(int(p[0]), int(p[1])) for p in meta.constraints["black_cells"]}
        assert exported_blacks == original_blacks

    def test_killer_round_trip_preserves_cage_sums(self):
        from richards_sudoku.services.text_format import export_text, import_text
        meta = _killer_meta()
        board = Board(size=9, variant=Variant.KILLER)
        board.cell(0, 0).value = 1
        vals = self._board_values(board)
        text = export_text(vals, meta.to_dict(), seed=0)
        bv2, md2, _, _ = import_text(text)
        assert bv2[0][0] == 1
        orig_sums = sorted(c["sum"] for c in meta.constraints["cages"])
        new_sums = sorted(c["sum"] for c in md2["constraints"]["cages"])
        assert orig_sums == new_sums


# ---------------------------------------------------------------------------
# T6: NewGameDialog smoke
# ---------------------------------------------------------------------------

class TestNewGameDialogSmoke:

    def test_dialog_instantiates(self, qtbot: QtBot):
        from richards_sudoku.ui.new_game_dialog import NewGameDialog
        dlg = NewGameDialog(initial_seed=0)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_dialog_has_required_properties(self, qtbot: QtBot):
        from richards_sudoku.ui.new_game_dialog import NewGameDialog
        dlg = NewGameDialog(initial_seed=0)
        qtbot.addWidget(dlg)
        # Must expose meta, difficulty, hint_limit, puzzle, solution
        for attr in ("meta", "difficulty", "hint_limit"):
            assert hasattr(dlg, attr), f"Missing property: {attr}"

    def test_dialog_title(self, qtbot: QtBot):
        from richards_sudoku.ui.new_game_dialog import NewGameDialog
        dlg = NewGameDialog(initial_seed=0)
        qtbot.addWidget(dlg)
        assert "New Game" in dlg.windowTitle()
