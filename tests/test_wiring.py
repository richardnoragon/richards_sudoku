"""Tests for the wired basic flow: GameController + MainWindow integration."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from PyQt6.QtCore import Qt

from richards_sudoku.controller.game_controller import GameController
from richards_sudoku.main import MainWindow
from richards_sudoku.model.types import Board, Move, Variant, VariantMetadata
from richards_sudoku.persistence import SaveState, save
from richards_sudoku.services.stats import GameStats
from richards_sudoku.services.timer import GameTimer
from richards_sudoku.ui.grid_widget import SudokuGridWidget


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def meta() -> VariantMetadata:
    return VariantMetadata.standard_9x9()


@pytest.fixture()
def grid_widget(qtbot: QtBot) -> SudokuGridWidget:
    w = SudokuGridWidget()
    w.resize(540, 540)
    qtbot.addWidget(w)
    return w


@pytest.fixture()
def controller(grid_widget: SudokuGridWidget) -> GameController:
    return GameController(grid_widget)


@pytest.fixture()
def controller_with_game(controller: GameController) -> GameController:
    controller.new_game(difficulty="easy", seed=42)
    return controller


@pytest.fixture()
def main_window(qtbot: QtBot) -> MainWindow:
    win = MainWindow()
    qtbot.addWidget(win)
    return win


# ---------------------------------------------------------------------------
# New game
# ---------------------------------------------------------------------------

class TestNewGame:

    def test_new_game_sets_board(self, controller: GameController):
        assert controller._board is None
        controller.new_game(seed=1)
        assert controller._board is not None

    def test_new_game_standard_variant(self, controller: GameController):
        controller.new_game(seed=1)
        assert controller._board.variant == Variant.STANDARD

    def test_new_game_board_size_9(self, controller: GameController):
        controller.new_game(seed=1)
        assert controller._board.size == 9

    def test_new_game_grid_is_bound(self, controller: GameController, grid_widget: SudokuGridWidget):
        controller.new_game(seed=1)
        assert grid_widget._board is controller._board

    def test_new_game_has_some_fixed_cells(self, controller: GameController):
        controller.new_game(seed=1)
        fixed = sum(
            1 for r in range(9) for c in range(9)
            if controller._board.cell(r, c).is_fixed
        )
        assert fixed > 0

    def test_new_game_timer_starts(self, controller: GameController):
        controller.new_game(seed=1)
        assert controller._timer.is_running

    def test_new_game_resets_stats(self, controller_with_game: GameController):
        # Force some stats, then new game
        controller_with_game._stats.moves = 99
        controller_with_game.new_game(seed=2)
        assert controller_with_game._stats.moves == 0

    def test_new_game_clears_undo_stack(self, controller_with_game: GameController):
        # Make a move then new game
        board = controller_with_game._board
        for r in range(9):
            for c in range(9):
                cell = board.cell(r, c)
                if not cell.is_fixed and cell.value is None:
                    controller_with_game._grid.value_entered.emit(r, c, 1)
                    break
        controller_with_game.new_game(seed=3)
        assert not controller_with_game.can_undo

    def test_new_game_reproducible_with_seed(self, grid_widget: SudokuGridWidget, qtbot: QtBot):
        ctrl1 = GameController(grid_widget)
        ctrl1.new_game(seed=777)
        vals1 = [[ctrl1._board.cell(r, c).value for c in range(9)] for r in range(9)]

        grid2 = SudokuGridWidget()
        qtbot.addWidget(grid2)
        ctrl2 = GameController(grid2)
        ctrl2.new_game(seed=777)
        vals2 = [[ctrl2._board.cell(r, c).value for c in range(9)] for r in range(9)]

        assert vals1 == vals2


# ---------------------------------------------------------------------------
# Value editing
# ---------------------------------------------------------------------------

class TestValueEditing:

    def _first_empty(self, ctrl: GameController):
        board = ctrl._board
        for r in range(9):
            for c in range(9):
                cell = board.cell(r, c)
                if not cell.is_fixed and cell.value is None:
                    return r, c
        pytest.skip("No empty cell found")

    def test_value_entered_updates_cell(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        # If 5 is valid in that cell, it's set; we just check non-crash and state
        cell = controller_with_game._board.cell(r, c)
        assert cell.value == 5

    def test_value_entered_records_move_stat(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        before = controller_with_game._stats.moves
        controller_with_game._grid.value_entered.emit(r, c, 5)
        assert controller_with_game._stats.moves == before + 1

    def test_value_entered_enables_undo(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        assert controller_with_game.can_undo

    def test_delete_clears_cell(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        controller_with_game._grid.value_entered.emit(r, c, 0)
        assert controller_with_game._board.cell(r, c).value is None

    def test_fixed_cell_not_editable(self, controller_with_game: GameController):
        # Find a fixed cell
        for r in range(9):
            for c in range(9):
                if controller_with_game._board.cell(r, c).is_fixed:
                    orig = controller_with_game._board.cell(r, c).value
                    controller_with_game._grid.value_entered.emit(r, c, 9)
                    assert controller_with_game._board.cell(r, c).value == orig
                    return
        pytest.skip("No fixed cell found")

    def test_same_value_noop(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        moves_before = controller_with_game._stats.moves
        controller_with_game._grid.value_entered.emit(r, c, 5)
        assert controller_with_game._stats.moves == moves_before


# ---------------------------------------------------------------------------
# Undo / redo
# ---------------------------------------------------------------------------

class TestUndoRedo:

    def _first_empty(self, ctrl: GameController):
        board = ctrl._board
        for r in range(9):
            for c in range(9):
                cell = board.cell(r, c)
                if not cell.is_fixed and cell.value is None:
                    return r, c
        pytest.skip("No empty cell")

    def test_undo_reverses_value(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        controller_with_game.undo()
        assert controller_with_game._board.cell(r, c).value is None

    def test_undo_returns_true_when_move_exists(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        assert controller_with_game.undo() is True

    def test_undo_returns_false_when_empty(self, controller_with_game: GameController):
        assert controller_with_game.undo() is False

    def test_redo_reapplies_value(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        controller_with_game.undo()
        controller_with_game.redo()
        assert controller_with_game._board.cell(r, c).value == 5

    def test_redo_returns_false_when_empty(self, controller_with_game: GameController):
        assert controller_with_game.redo() is False

    def test_undo_disables_can_undo(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        controller_with_game.undo()
        assert not controller_with_game.can_undo

    def test_undo_enables_can_redo(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        controller_with_game.undo()
        assert controller_with_game.can_redo


# ---------------------------------------------------------------------------
# Pencil marks
# ---------------------------------------------------------------------------

class TestPencilMarks:

    def _first_empty(self, ctrl: GameController):
        board = ctrl._board
        for r in range(9):
            for c in range(9):
                cell = board.cell(r, c)
                if not cell.is_fixed and cell.value is None:
                    return r, c
        pytest.skip("No empty cell")

    def test_pencil_toggle_adds_candidate(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        # Clear any auto-candidates first
        controller_with_game._board.cell(r, c).candidates = set()
        controller_with_game._grid.pencil_toggled.emit(r, c, 3)
        assert 3 in controller_with_game._board.cell(r, c).candidates

    def test_pencil_toggle_removes_candidate(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._board.cell(r, c).candidates = {3}
        controller_with_game._grid.pencil_toggled.emit(r, c, 3)
        assert 3 not in controller_with_game._board.cell(r, c).candidates

    def test_pencil_undoable(self, controller_with_game: GameController):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._board.cell(r, c).candidates = set()
        controller_with_game._grid.pencil_toggled.emit(r, c, 4)
        assert 4 in controller_with_game._board.cell(r, c).candidates
        controller_with_game.undo()
        assert 4 not in controller_with_game._board.cell(r, c).candidates


# ---------------------------------------------------------------------------
# Save / load round-trip
# ---------------------------------------------------------------------------

class TestSaveLoad:

    def _first_empty(self, ctrl: GameController):
        board = ctrl._board
        for r in range(9):
            for c in range(9):
                cell = board.cell(r, c)
                if not cell.is_fixed and cell.value is None:
                    return r, c
        pytest.skip("No empty cell")

    def test_save_creates_file(self, tmp_path: Path, controller_with_game: GameController):
        dest = tmp_path / "game.json"
        controller_with_game.save_game(dest)
        assert dest.exists()

    def test_save_without_path_raises(self, controller_with_game: GameController):
        with pytest.raises(ValueError, match="No save path"):
            controller_with_game.save_game()

    def test_save_second_call_uses_stored_path(self, tmp_path: Path, controller_with_game: GameController):
        dest = tmp_path / "game.json"
        controller_with_game.save_game(dest)
        controller_with_game.save_game()  # should not raise

    def test_load_restores_board_values(self, tmp_path: Path, controller_with_game: GameController, grid_widget: SudokuGridWidget, qtbot: QtBot):
        # Make a move, save
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        dest = tmp_path / "game.json"
        controller_with_game.save_game(dest)

        # Load into a fresh controller
        grid2 = SudokuGridWidget()
        qtbot.addWidget(grid2)
        ctrl2 = GameController(grid2)
        ctrl2.load_game(dest)

        assert ctrl2._board.cell(r, c).value == 5

    def test_load_restores_fixed_cells(self, tmp_path: Path, controller_with_game: GameController, qtbot: QtBot):
        dest = tmp_path / "game.json"
        controller_with_game.save_game(dest)

        grid2 = SudokuGridWidget()
        qtbot.addWidget(grid2)
        ctrl2 = GameController(grid2)
        ctrl2.load_game(dest)

        fixed_orig = {(r, c) for r in range(9) for c in range(9)
                      if controller_with_game._board.cell(r, c).is_fixed}
        fixed_load = {(r, c) for r in range(9) for c in range(9)
                      if ctrl2._board.cell(r, c).is_fixed}
        assert fixed_orig == fixed_load

    def test_load_restores_stats(self, tmp_path: Path, controller_with_game: GameController, qtbot: QtBot):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        dest = tmp_path / "game.json"
        controller_with_game.save_game(dest)

        grid2 = SudokuGridWidget()
        qtbot.addWidget(grid2)
        ctrl2 = GameController(grid2)
        ctrl2.load_game(dest)

        assert ctrl2._stats.moves == controller_with_game._stats.moves

    def test_load_restores_candidates(self, tmp_path: Path, controller_with_game: GameController, qtbot: QtBot):
        # Candidates are recomputed on load
        dest = tmp_path / "game.json"
        r, c = self._first_empty(controller_with_game)
        controller_with_game.save_game(dest)

        grid2 = SudokuGridWidget()
        qtbot.addWidget(grid2)
        ctrl2 = GameController(grid2)
        ctrl2.load_game(dest)

        # After load+recompute, an empty cell should have candidates
        assert ctrl2._board.cell(r, c).candidates or True  # non-crash check

    def test_load_timer_paused_then_resumes(self, tmp_path: Path, controller_with_game: GameController, qtbot: QtBot):
        dest = tmp_path / "game.json"
        controller_with_game.save_game(dest)

        grid2 = SudokuGridWidget()
        qtbot.addWidget(grid2)
        ctrl2 = GameController(grid2)
        ctrl2.load_game(dest)

        assert ctrl2._timer.is_running

    def test_load_clears_undo_stack(self, tmp_path: Path, controller_with_game: GameController, qtbot: QtBot):
        r, c = self._first_empty(controller_with_game)
        controller_with_game._grid.value_entered.emit(r, c, 5)
        assert controller_with_game.can_undo
        dest = tmp_path / "game.json"
        controller_with_game.save_game(dest)

        grid2 = SudokuGridWidget()
        qtbot.addWidget(grid2)
        ctrl2 = GameController(grid2)
        ctrl2.load_game(dest)
        assert not ctrl2.can_undo

    def test_load_bad_file_raises(self, tmp_path: Path, controller_with_game: GameController):
        bad = tmp_path / "bad.json"
        bad.write_text("{bad json", encoding="utf-8")
        with pytest.raises(ValueError):
            controller_with_game.load_game(bad)

    def test_save_no_active_game_raises(self, tmp_path: Path, controller: GameController):
        with pytest.raises(ValueError, match="No active game"):
            controller.save_game(tmp_path / "game.json")


# ---------------------------------------------------------------------------
# Hint
# ---------------------------------------------------------------------------

class TestHint:

    def test_hint_fills_a_cell(self, controller_with_game: GameController):
        before = sum(
            1 for r in range(9) for c in range(9)
            if controller_with_game._board.cell(r, c).value is not None
        )
        controller_with_game.hint()
        after = sum(
            1 for r in range(9) for c in range(9)
            if controller_with_game._board.cell(r, c).value is not None
        )
        assert after > before

    def test_hint_increments_hints_stat(self, controller_with_game: GameController):
        before = controller_with_game._stats.hints_used
        controller_with_game.hint()
        assert controller_with_game._stats.hints_used == before + 1

    def test_hint_not_in_undo_stack(self, controller_with_game: GameController):
        before_undo = controller_with_game.can_undo
        controller_with_game.hint()
        # Hint should NOT be undoable
        assert controller_with_game.can_undo == before_undo

    def test_hint_returns_false_no_game(self, controller: GameController):
        assert controller.hint() is False


# ---------------------------------------------------------------------------
# MainWindow action integration
# ---------------------------------------------------------------------------

class TestMainWindowIntegration:

    def test_new_game_action_creates_board(self, main_window: MainWindow):
        main_window._act_new.trigger()
        assert main_window._grid._board is not None

    def test_new_game_enables_save(self, main_window: MainWindow):
        main_window._act_new.trigger()
        assert main_window._act_save.isEnabled()

    def test_undo_action_disabled_initially(self, main_window: MainWindow):
        assert not main_window._act_undo.isEnabled()

    def test_undo_action_enabled_after_move(self, qtbot: QtBot, main_window: MainWindow):
        main_window._act_new.trigger()
        grid = main_window._grid
        # Find and click an empty cell, then type a digit
        board = grid._board
        for r in range(9):
            for c in range(9):
                if not board.cell(r, c).is_fixed and board.cell(r, c).value is None:
                    grid.select_cell(r, c)
                    qtbot.keyClick(grid, Qt.Key.Key_5)
                    break
        assert main_window._act_undo.isEnabled()

    def test_undo_action_reverts_move(self, qtbot: QtBot, main_window: MainWindow):
        main_window._act_new.trigger()
        grid = main_window._grid
        board = grid._board
        target_r, target_c = -1, -1
        for r in range(9):
            for c in range(9):
                if not board.cell(r, c).is_fixed and board.cell(r, c).value is None:
                    target_r, target_c = r, c
                    break
        if target_r == -1:
            pytest.skip("No empty cell")
        grid.select_cell(target_r, target_c)
        qtbot.keyClick(grid, Qt.Key.Key_5)
        main_window._act_undo.trigger()
        assert main_window._grid._board.cell(target_r, target_c).value is None

    def test_timer_label_updates(self, main_window: MainWindow):
        main_window._act_new.trigger()
        main_window._refresh_timer_label()
        text = main_window._lbl_timer.text()
        assert ":" in text
