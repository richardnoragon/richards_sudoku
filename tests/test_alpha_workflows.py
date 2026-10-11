"""Regression coverage for the documented Alpha workflow blockers."""
import json

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from sudoku_inator.controller.game_controller import GameController
from sudoku_inator.main import MainWindow
from sudoku_inator.model.types import Board, Variant, VariantMetadata
from sudoku_inator.ui.grid_widget import SudokuGridWidget


@pytest.fixture
def ctrl(qtbot):
    grid = SudokuGridWidget()
    qtbot.addWidget(grid)
    controller = GameController(grid)
    controller.new_game(seed=42, difficulty="easy")
    return controller


@pytest.fixture
def window(qtbot, monkeypatch):
    win = MainWindow()
    qtbot.addWidget(win)
    # Teardown may close an edited window; individual guard tests override this.
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Discard)
    return win


def empty(ctrl):
    return next((r, c) for r in range(ctrl._board.size) for c in range(ctrl._board.size)
                if ctrl._board.cell(r, c).value is None and not ctrl._board.cell(r, c).is_black)


def test_resume_preserves_hints_notes_and_restart_puzzle(ctrl, tmp_path):
    original = [row[:] for row in ctrl._puzzle_grid]
    ctrl.hint()
    r, c = empty(ctrl)
    ctrl._board.cell(r, c).candidates = {2, 7}
    dest = tmp_path / "session.json"
    ctrl.save_game(dest)
    ctrl.new_game(seed=9)
    ctrl.load_game(dest)
    assert ctrl.hints_remaining == 2
    assert ctrl._board.cell(r, c).candidates == {2, 7}
    assert not ctrl.can_undo  # history is deliberately session-local
    ctrl.restart_game()
    assert [[cell.value for cell in row] for row in ctrl._board.cells] == original


def test_legacy_allowance_derived_from_usage(ctrl, tmp_path):
    ctrl.hint()
    dest = tmp_path / "old.json"
    ctrl.save_game(dest)
    data = json.loads(dest.read_text())
    data.pop("original_puzzle", None)
    dest.write_text(json.dumps(data))
    ctrl.load_game(dest)
    assert ctrl.hints_remaining == 2
    assert ctrl._puzzle_grid is not None


def test_save_failure_keeps_timer_and_dirty_state(ctrl, tmp_path, monkeypatch):
    ctrl._grid.value_entered.emit(*empty(ctrl), 4)
    monkeypatch.setattr("sudoku_inator.controller.game_controller.save",
                        lambda *a: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):
        ctrl.save_game(tmp_path / "fail.json")
    assert ctrl._timer.is_running
    assert ctrl.is_dirty
    assert ctrl.save_path is None


def test_failed_load_preserves_current_session(ctrl, tmp_path):
    board = ctrl._board
    dest = tmp_path / "bad.json"
    ctrl.save_game(dest)
    data = json.loads(dest.read_text())
    data["board"]["cells"][0][0]["value"] = 100
    dest.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        ctrl.load_game(dest)
    assert ctrl._board is board


def test_elimination_survives_undo_redo(ctrl):
    r, c = empty(ctrl)
    ctrl._grid.select_cell(r, c)
    solution = ctrl._solution[r][c]
    wrong = 1 if solution != 1 else 2
    ctrl._board.cell(r, c).candidates = {solution, wrong}
    assert ctrl.hint("eliminate")
    assert ctrl._board.cell(r, c).candidates == {solution}
    ctrl.undo()
    assert ctrl._board.cell(r, c).candidates == {solution, wrong}
    ctrl.redo()
    assert ctrl._board.cell(r, c).candidates == {solution}


def test_unknown_hint_cannot_spend_allowance(ctrl):
    before = ctrl._board.to_dict()
    assert not ctrl.hint("misspelled")
    assert ctrl.hints_remaining == 3
    assert ctrl._board.to_dict() == before


def test_large_board_value_dialog_pencil_and_undo(qtbot, monkeypatch):
    grid = SudokuGridWidget()
    qtbot.addWidget(grid)
    ctrl = GameController(grid)
    meta = VariantMetadata(Variant.ONE_TO_25, 25, list(range(1, 26)),
                           [[r // 5 * 5 + c // 5 for c in range(25)] for r in range(25)])
    ctrl._meta, ctrl._board = meta, Board(25, Variant.ONE_TO_25)
    grid.set_board(ctrl._board, meta)
    grid.select_cell(0, 0)
    monkeypatch.setattr(QInputDialog, "getInt", lambda *a, **k: (25, True))
    qtbot.keyClick(grid, Qt.Key.Key_F4)
    assert ctrl._board.cell(0, 0).value == 25
    ctrl.undo()
    assert ctrl._board.cell(0, 0).value is None
    ctrl.redo()
    qtbot.keyClick(grid, Qt.Key.Key_Delete)
    ctrl._board.cell(0, 0).candidates.clear()
    grid.set_pencil_mode(True)
    qtbot.keyClick(grid, Qt.Key.Key_F4)
    assert 25 in ctrl._board.cell(0, 0).candidates
    ctrl.undo()
    assert 25 not in ctrl._board.cell(0, 0).candidates


def test_codebook_hidden_editable_undoable_and_saved(window, tmp_path):
    ctrl = window._ctrl
    ctrl._meta.name = Variant.CODEWORDS
    ctrl._board.variant = Variant.CODEWORDS
    ctrl._meta.constraints = {"codebook": dict(zip("ABCDEFGHI", range(1, 10))),
                              "given_mappings": {"A": 1}}
    window._refresh_codebook_panel(ctrl.variant_meta)
    assert window._codebook_fields[0].text() == "1"
    assert window._codebook_fields[0].isReadOnly()
    field = window._codebook_fields[1]
    assert field.text() == ""
    assert not field.isReadOnly()
    field.setText("3")
    field.editingFinished.emit()
    assert ctrl._board.codebook_hypotheses == {"B": 3}
    window._on_undo()
    assert field.text() == ""
    window._on_redo()
    assert field.text() == "3"
    ctrl.save_game(tmp_path / "codewords.json")
    ctrl.load_game(tmp_path / "codewords.json")
    assert ctrl._board.codebook_hypotheses == {"B": 3}
    assert ctrl._meta.constraints["codebook"]["B"] == 2


def test_export_import_actions_round_trip(window, tmp_path, monkeypatch):
    dest = tmp_path / "puzzle.txt"
    original = window._ctrl._board.to_dict()
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(dest), "Puzzle text (*.txt)"))
    window._act_export.trigger()
    assert dest.exists()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(dest), ""))
    window._act_import.trigger()
    assert [[cell.value for cell in row] for row in window._ctrl._board.cells] == [
        [cell["value"] for cell in row] for row in original["cells"]]
    assert window._ctrl.save_path is None


def test_check_action_reports_conflicts(window):
    r, c = empty(window._ctrl)
    other = next(cell.value for cell in window._ctrl._board.cells[r] if cell.value)
    window._ctrl._grid.value_entered.emit(r, c, other)
    window._act_check.trigger()
    assert "conflict" in window.statusBar().currentMessage().lower()


@pytest.mark.parametrize("action", ["open", "new", "restart", "import", "close"])
def test_cancel_protects_unsaved_progress(window, monkeypatch, action):
    ctrl = window._ctrl
    ctrl._grid.value_entered.emit(*empty(ctrl), 4)
    board = ctrl._board.to_dict()
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Cancel)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: pytest.fail("Opened dialog after cancel"))
    if action == "close":
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()
        window.closeEvent(event)
        assert not event.isAccepted()
    else:
        getattr(window, "_act_" + action).trigger()
    assert ctrl._board.to_dict() == board


def test_cancelled_save_does_not_allow_discard(window, monkeypatch):
    window._ctrl._grid.value_entered.emit(*empty(window._ctrl), 4)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Save)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
    assert not window._confirm_discard()
    assert window._ctrl.is_dirty


@pytest.mark.parametrize("worker_name,size", [
    ("JigsawWorker", 9), ("Str8tsWorker", 9), ("KillerWorker", 9),
    ("OneToTwentyFiveWorker", 25), ("CodewordsWorker", 9),
    ("KenKenWorker", 4), ("KenKenWorker", 6), ("KenKenWorker", 9), ("KakuroWorker", 9),
])
def test_generated_variant_play_save_resume_complete(qtbot, tmp_path, worker_name, size):
    from sudoku_inator.ui import new_game_dialog
    from sudoku_inator.services.validation import conflict_cells
    worker_class = getattr(new_game_dialog, worker_name)
    kwargs = {"size": size} if worker_name == "KenKenWorker" else {}
    worker = worker_class(42, "hard" if size == 25 else "easy", [False], **kwargs)
    results, errors = [], []
    worker.finished.connect(lambda *args: results.append(args))
    worker.error.connect(errors.append)
    worker.failed.connect(errors.append)
    worker.run()
    assert results and not errors, errors
    meta, puzzle, solution = results[0]
    grid = SudokuGridWidget()
    qtbot.addWidget(grid)
    ctrl = GameController(grid)
    ctrl.new_game(meta, puzzle=puzzle, solution=solution)
    assert [[cell.value for cell in row] for row in ctrl._board.cells] == puzzle
    assert not conflict_cells(ctrl._board, meta)
    if worker_name in ("Str8tsWorker", "KillerWorker", "KenKenWorker", "KakuroWorker"):
        from sudoku_inator.solver.variant_search import count_variant_solutions
        assert count_variant_solutions(meta, puzzle, max_nodes=10000) == 1
    r, c = empty(ctrl)
    grid.value_entered.emit(r, c, solution[r][c])
    ctrl.save_game(tmp_path / "variant.json")
    ctrl.load_game(tmp_path / "variant.json")
    assert ctrl._board.cell(r, c).value == solution[r][c]
    complete = []
    ctrl.set_complete_callback(lambda: complete.append(True))
    remaining = [(r, c) for r in range(size) for c in range(size)
                 if ctrl._board.cell(r, c).value is None and not ctrl._board.cell(r, c).is_black]
    # Arrange the last-move scenario without hundreds of identical UI emissions.
    for r, c in remaining[:-1]:
        ctrl._board.cell(r, c).value = solution[r][c]
    r, c = remaining[-1]
    grid.value_entered.emit(r, c, solution[r][c])
    assert ctrl.is_complete
    assert complete == [True]
    assert not ctrl._timer.is_running
    ctrl.save_game(tmp_path / "complete.json")
    ctrl.load_game(tmp_path / "complete.json")
    assert not ctrl._timer.is_running
    ctrl.restart_game()
    assert [[cell.value for cell in row] for row in ctrl._board.cells] == puzzle


def test_new_game_uses_dialog_result_without_regenerating(window, monkeypatch):
    from PyQt6.QtWidgets import QDialog
    from sudoku_inator.main import NewGameDialog
    puzzle = [row[:] for row in window._ctrl._puzzle_grid]
    solution = [row[:] for row in window._ctrl._solution]
    meta = window._ctrl.variant_meta
    monkeypatch.setattr(NewGameDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    for name, value in [("puzzle", puzzle), ("solution", solution), ("meta", meta)]:
        monkeypatch.setattr(NewGameDialog, name, property(lambda self, v=value: v))
    monkeypatch.setattr("sudoku_inator.controller.game_controller.generate_puzzle",
                        lambda *a, **k: pytest.fail("Regenerated the worker result"))
    window._act_new.trigger()
    assert window._ctrl._puzzle_grid == puzzle


def test_variant_counter_handles_ambiguity_budget_and_cancel():
    from sudoku_inator.solver.variant_search import count_variant_solutions
    meta = VariantMetadata(Variant.KENKEN, 4, [1, 2, 3, 4],
                           [[r * 4 + c for c in range(4)] for r in range(4)],
                           {"has_box_regions": False})
    blank = [[None] * 4 for _ in range(4)]
    assert count_variant_solutions(meta, blank) == 2
    assert count_variant_solutions(meta, blank, max_nodes=0) is None
    assert count_variant_solutions(meta, blank, cancel_flag=[True]) is None
    # Two completions of a four-cell Kakuro square, with no global Sudoku units.
    meta = VariantMetadata(Variant.KAKURO, 4, list(range(1, 10)),
                           [[r * 4 + c for c in range(4)] for r in range(4)],
                           {"black_cells": [[r, c] for r in range(4) for c in range(4)
                                            if r not in (1, 2) or c not in (1, 2)],
                            "clues": [{"cells": cells, "sum": 3, "dir": direction} for cells, direction in [
                                ([[1, 1], [1, 2]], "across"), ([[2, 1], [2, 2]], "across"),
                                ([[1, 1], [2, 1]], "down"), ([[1, 2], [2, 2]], "down")]]})
    assert count_variant_solutions(meta, blank) == 2
    blank[1][1] = 1
    assert count_variant_solutions(meta, blank) == 1
    blank[1][2] = 1
    assert count_variant_solutions(meta, blank) == 0


def test_failed_import_and_save_keep_progress(window, tmp_path, monkeypatch):
    window._ctrl._grid.value_entered.emit(*empty(window._ctrl), 4)
    before = window._ctrl._board.to_dict()
    messages = []
    monkeypatch.setattr(QMessageBox, "critical", lambda *a: messages.append(a[2]))
    bad = tmp_path / "bad.txt"
    bad.write_text("not a puzzle")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a: (str(bad), ""))
    window._act_import.trigger()
    assert messages and window._ctrl._board.to_dict() == before
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: QMessageBox.StandardButton.Save)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a: (str(tmp_path / "save.json"), ""))
    monkeypatch.setattr(window._ctrl, "save_game", lambda *a: (_ for _ in ()).throw(OSError("disk full")))
    assert not window._confirm_discard()
    assert window._ctrl.is_dirty


def test_atomic_save_failure_preserves_original_and_backup(ctrl, tmp_path, monkeypatch):
    from sudoku_inator.persistence.persistence import load
    path = tmp_path / "session.json"
    ctrl.save_game(path)
    before = path.read_bytes()
    ctrl._grid.value_entered.emit(*empty(ctrl), 4)
    monkeypatch.setattr("sudoku_inator.persistence.persistence.os.replace",
                        lambda *a: (_ for _ in ()).throw(OSError("replace failed")))
    with pytest.raises(OSError):
        ctrl.save_game()
    assert path.read_bytes() == before
    assert path.with_suffix(".json.bak").read_bytes() == before
    assert load(path).board.to_dict() != ctrl._board.to_dict()
    assert not list(tmp_path.glob("*.tmp"))


def test_hint_drops_obsolete_edits_but_not_unrelated_undo(ctrl):
    r, c = empty(ctrl)
    ctrl._grid.select_cell(r, c)
    ctrl._grid.pencil_toggled.emit(r, c, 4)
    assert ctrl.can_undo
    ctrl.hint("reveal_cell")
    assert ctrl._board.cell(r, c).is_fixed
    assert not ctrl.can_undo
    assert ctrl.hints_remaining == 2


def test_undo_completion_resumes_and_redo_completes(ctrl):
    cells = [(r, c) for r in range(9) for c in range(9)
             if ctrl._board.cell(r, c).value is None]
    for r, c in cells[:-1]:
        ctrl._board.cell(r, c).value = ctrl._solution[r][c]
    events = []
    ctrl.set_complete_callback(lambda: events.append(True))
    r, c = cells[-1]
    ctrl._grid.value_entered.emit(r, c, ctrl._solution[r][c])
    assert ctrl.is_complete and not ctrl._timer.is_running
    ctrl.undo()
    assert not ctrl.is_complete and ctrl._timer.is_running
    ctrl.redo()
    assert ctrl.is_complete and not ctrl._timer.is_running
    assert events == [True, True]
