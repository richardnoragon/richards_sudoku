"""Tests for the services layer: candidates, undo/redo, timer, stats."""
from __future__ import annotations

import time

import pytest

from richards_sudoku.model.types import Board, Cell, Move, Variant, VariantMetadata
from richards_sudoku.services import (
    GameStats,
    GameTimer,
    UndoRedoStack,
    compute_candidates,
    update_all_candidates,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _standard_meta() -> VariantMetadata:
    return VariantMetadata.standard_9x9()


def _empty_board() -> Board:
    return Board(size=9, variant=Variant.STANDARD)


def _board_with_row(row_values: list[int | None]) -> Board:
    """Return a board whose first row is pre-filled with row_values (length 9)."""
    board = _empty_board()
    for c, v in enumerate(row_values):
        board.cell(0, c).value = v
    return board


def _make_move(
    row: int,
    col: int,
    old_value: int | None,
    new_value: int | None,
    old_cands: frozenset[int] | None = None,
    new_cands: frozenset[int] | None = None,
) -> Move:
    return Move(
        row=row,
        col=col,
        old_value=old_value,
        new_value=new_value,
        old_candidates=old_cands or frozenset(),
        new_candidates=new_cands or frozenset(),
    )


# ---------------------------------------------------------------------------
# compute_candidates
# ---------------------------------------------------------------------------

class TestComputeCandidates:

    def test_empty_board_corner_returns_all_symbols(self):
        board = _empty_board()
        meta = _standard_meta()
        cands = compute_candidates(board, 0, 0, meta)
        assert cands == set(range(1, 10))

    def test_row_peers_excluded(self):
        board = _empty_board()
        meta = _standard_meta()
        # Fill row 0 with 1-8; cell (0,8) should only have candidate 9
        for c in range(8):
            board.cell(0, c).value = c + 1
        cands = compute_candidates(board, 0, 8, meta)
        assert cands == {9}

    def test_column_peers_excluded(self):
        board = _empty_board()
        meta = _standard_meta()
        for r in range(8):
            board.cell(r, 0).value = r + 1
        cands = compute_candidates(board, 8, 0, meta)
        assert cands == {9}

    def test_box_peers_excluded(self):
        board = _empty_board()
        meta = _standard_meta()
        # Fill top-left 3×3 box except (2,2)
        vals = iter(range(1, 9))
        for r in range(3):
            for c in range(3):
                if not (r == 2 and c == 2):
                    board.cell(r, c).value = next(vals)
        cands = compute_candidates(board, 2, 2, meta)
        assert cands == {9}

    def test_filled_cell_returns_empty_set(self):
        board = _empty_board()
        meta = _standard_meta()
        board.cell(0, 0).value = 5
        cands = compute_candidates(board, 0, 0, meta)
        assert cands == set()

    def test_no_candidates_when_all_symbols_blocked(self):
        board = _empty_board()
        meta = _standard_meta()
        # Block all nine symbols in row 0, column 0, or box 0
        # Row 0: cols 1-8 get values 1-8; col 0 row 1-8 have value 9 → no room
        for c in range(1, 9):
            board.cell(0, c).value = c  # row blocks 1-8
        board.cell(1, 0).value = 9      # column + another block for 9
        # (0,0) peers in box cover (1,0)=9; row blocks 1-8 → zero candidates
        cands = compute_candidates(board, 0, 0, meta)
        assert cands == set()


class TestUpdateAllCandidates:

    def test_sets_candidates_on_all_empty_cells(self):
        board = _empty_board()
        meta = _standard_meta()
        # Initially all candidates are empty sets
        assert board.cell(0, 0).candidates == set()
        update_all_candidates(board, meta)
        # After update every empty cell should have non-empty candidates
        for r in range(9):
            for c in range(9):
                assert board.cell(r, c).candidates == set(range(1, 10))

    def test_clears_candidates_for_filled_cells(self):
        board = _empty_board()
        meta = _standard_meta()
        board.cell(0, 0).value = 5
        update_all_candidates(board, meta)
        assert board.cell(0, 0).candidates == set()

    def test_skips_fixed_cells(self):
        board = _empty_board()
        meta = _standard_meta()
        board.cell(0, 0).is_fixed = True
        board.cell(0, 0).candidates = {1, 2, 3}  # pre-existing garbage
        update_all_candidates(board, meta)
        # Fixed cell with no value should not be touched
        assert board.cell(0, 0).candidates == {1, 2, 3}

    def test_row_constraints_propagate(self):
        board = _empty_board()
        meta = _standard_meta()
        for c in range(1, 9):
            board.cell(0, c).value = c  # cols 1-8 have values 1-8
        update_all_candidates(board, meta)
        # Only 9 is left as candidate for (0, 0)
        assert board.cell(0, 0).candidates == {9}


# ---------------------------------------------------------------------------
# UndoRedoStack
# ---------------------------------------------------------------------------

class TestUndoRedoStack:

    def test_initial_state(self):
        stack = UndoRedoStack()
        assert not stack.can_undo
        assert not stack.can_redo

    def test_push_enables_undo(self):
        stack = UndoRedoStack()
        move = _make_move(0, 0, None, 5)
        stack.push(move)
        assert stack.can_undo
        assert not stack.can_redo

    def test_undo_applies_reverse_to_board(self):
        board = _empty_board()
        board.cell(0, 0).value = 5
        stack = UndoRedoStack()
        move = _make_move(0, 0, None, 5)
        stack.push(move)
        result = stack.undo(board)
        assert result is move
        assert board.cell(0, 0).value is None

    def test_undo_enables_redo(self):
        board = _empty_board()
        board.cell(0, 0).value = 5
        stack = UndoRedoStack()
        stack.push(_make_move(0, 0, None, 5))
        stack.undo(board)
        assert not stack.can_undo
        assert stack.can_redo

    def test_redo_reapplies_move(self):
        board = _empty_board()
        board.cell(0, 0).value = 5
        stack = UndoRedoStack()
        move = _make_move(0, 0, None, 5)
        stack.push(move)
        stack.undo(board)
        result = stack.redo(board)
        assert result is move
        assert board.cell(0, 0).value == 5

    def test_redo_enables_undo(self):
        board = _empty_board()
        board.cell(0, 0).value = 5
        stack = UndoRedoStack()
        stack.push(_make_move(0, 0, None, 5))
        stack.undo(board)
        stack.redo(board)
        assert stack.can_undo
        assert not stack.can_redo

    def test_new_push_clears_redo(self):
        board = _empty_board()
        board.cell(0, 0).value = 5
        stack = UndoRedoStack()
        stack.push(_make_move(0, 0, None, 5))
        stack.undo(board)
        assert stack.can_redo
        stack.push(_make_move(0, 1, None, 3))
        assert not stack.can_redo

    def test_undo_empty_returns_none(self):
        board = _empty_board()
        stack = UndoRedoStack()
        assert stack.undo(board) is None

    def test_redo_empty_returns_none(self):
        board = _empty_board()
        stack = UndoRedoStack()
        assert stack.redo(board) is None

    def test_multiple_undo_redo_sequence(self):
        board = _empty_board()
        stack = UndoRedoStack()
        moves = [
            _make_move(0, 0, None, 1),
            _make_move(0, 1, None, 2),
            _make_move(0, 2, None, 3),
        ]
        board.cell(0, 0).value = 1
        stack.push(moves[0])
        board.cell(0, 1).value = 2
        stack.push(moves[1])
        board.cell(0, 2).value = 3
        stack.push(moves[2])

        stack.undo(board)
        stack.undo(board)
        assert board.cell(0, 2).value is None
        assert board.cell(0, 1).value is None
        assert board.cell(0, 0).value == 1

        stack.redo(board)
        assert board.cell(0, 1).value == 2

    def test_pencil_mark_undo(self):
        board = _empty_board()
        board.cell(0, 0).candidates = {1, 2, 3}
        stack = UndoRedoStack()
        move = Move(
            row=0, col=0,
            old_value=None, new_value=None,
            old_candidates=frozenset(),
            new_candidates=frozenset({1, 2, 3}),
        )
        stack.push(move)
        stack.undo(board)
        assert board.cell(0, 0).candidates == set()

    def test_clear_resets_both_stacks(self):
        board = _empty_board()
        board.cell(0, 0).value = 5
        stack = UndoRedoStack()
        stack.push(_make_move(0, 0, None, 5))
        stack.undo(board)
        stack.clear()
        assert not stack.can_undo
        assert not stack.can_redo


# ---------------------------------------------------------------------------
# GameTimer
# ---------------------------------------------------------------------------

class TestGameTimer:

    def test_initial_not_running(self):
        timer = GameTimer()
        assert not timer.is_running
        assert timer.elapsed_seconds() == pytest.approx(0.0)

    def test_start_sets_running(self):
        timer = GameTimer()
        timer.start()
        assert timer.is_running

    def test_elapsed_increases_while_running(self):
        timer = GameTimer()
        timer.start()
        time.sleep(0.05)
        assert timer.elapsed_seconds() > 0.0

    def test_pause_stops_accumulation(self):
        timer = GameTimer()
        timer.start()
        time.sleep(0.05)
        timer.pause()
        elapsed_at_pause = timer.elapsed_seconds()
        assert not timer.is_running
        time.sleep(0.05)
        # Elapsed should not increase after pause
        assert timer.elapsed_seconds() == pytest.approx(elapsed_at_pause)

    def test_resume_continues_accumulation(self):
        timer = GameTimer()
        timer.start()
        time.sleep(0.05)
        timer.pause()
        elapsed_before = timer.elapsed_seconds()
        time.sleep(0.02)
        timer.resume()
        time.sleep(0.05)
        assert timer.elapsed_seconds() > elapsed_before

    def test_reset_zeroes_timer(self):
        timer = GameTimer()
        timer.start()
        time.sleep(0.05)
        timer.reset()
        assert not timer.is_running
        assert timer.elapsed_seconds() == pytest.approx(0.0)

    def test_start_noop_when_running(self):
        timer = GameTimer()
        timer.start()
        time.sleep(0.05)
        t1 = timer.elapsed_seconds()
        timer.start()  # should not reset elapsed
        assert timer.elapsed_seconds() >= t1

    def test_pause_noop_when_paused(self):
        timer = GameTimer()
        timer.start()
        time.sleep(0.05)
        timer.pause()
        t1 = timer.elapsed_seconds()
        timer.pause()  # second pause must not change accumulated
        assert timer.elapsed_seconds() == pytest.approx(t1)

    def test_resume_noop_when_running(self):
        timer = GameTimer()
        timer.start()
        timer.resume()  # should be a no-op
        assert timer.is_running

    def test_round_trip_serialisation(self):
        timer = GameTimer()
        timer.start()
        time.sleep(0.05)
        timer.pause()
        d = timer.to_dict()
        restored = GameTimer.from_dict(d)
        assert not restored.is_running
        assert restored.elapsed_seconds() == pytest.approx(timer.elapsed_seconds(), abs=1e-6)

    def test_from_dict_always_paused(self):
        d = {"elapsed_seconds": 42.5, "is_running": True}
        restored = GameTimer.from_dict(d)
        assert not restored.is_running
        assert restored.elapsed_seconds() == pytest.approx(42.5)


# ---------------------------------------------------------------------------
# GameStats
# ---------------------------------------------------------------------------

class TestGameStats:

    def test_initial_zeros(self):
        stats = GameStats()
        assert stats.moves == 0
        assert stats.hints_used == 0
        assert stats.elapsed_seconds == pytest.approx(0.0)

    def test_record_move_increments(self):
        stats = GameStats()
        stats.record_move()
        stats.record_move()
        assert stats.moves == 2

    def test_record_hint_increments(self):
        stats = GameStats()
        stats.record_hint()
        assert stats.hints_used == 1

    def test_set_completion_time(self):
        stats = GameStats()
        stats.set_completion_time(123.45)
        assert stats.elapsed_seconds == pytest.approx(123.45)

    def test_round_trip_serialisation(self):
        stats = GameStats(moves=10, hints_used=3, elapsed_seconds=99.9)
        d = stats.to_dict()
        restored = GameStats.from_dict(d)
        assert restored.moves == 10
        assert restored.hints_used == 3
        assert restored.elapsed_seconds == pytest.approx(99.9)

    def test_from_dict_type_coercion(self):
        d = {"moves": "5", "hints_used": "2", "elapsed_seconds": "10.0"}
        stats = GameStats.from_dict(d)
        assert stats.moves == 5
        assert stats.hints_used == 2
        assert stats.elapsed_seconds == pytest.approx(10.0)
