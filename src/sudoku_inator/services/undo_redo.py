"""Undo/redo stack service.

Only board value changes and pencil-mark changes are tracked.
Timer state and hint counters are intentionally excluded.
"""
from __future__ import annotations

from sudoku_inator.model.types import Board, CodebookMove, Move


class UndoRedoStack:
    """Manages undo and redo stacks for board and pencil-mark moves."""

    def __init__(self) -> None:
        self._undo: list[Move | CodebookMove] = []
        self._redo: list[Move | CodebookMove] = []

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------

    def push(self, move: Move | CodebookMove) -> None:
        """Record a new move and clear the redo stack."""
        self._undo.append(move)
        self._redo.clear()

    def undo(self, board: Board) -> Move | CodebookMove | None:
        """Reverse the most recent move on *board* and return it, or None."""
        if not self._undo:
            return None
        move = self._undo.pop()
        board.reverse_move(move)
        self._redo.append(move)
        return move

    def redo(self, board: Board) -> Move | CodebookMove | None:
        """Re-apply the most recently undone move on *board* and return it, or None."""
        if not self._redo:
            return None
        move = self._redo.pop()
        board.apply_move(move)
        self._undo.append(move)
        return move

    def discard_cell(self, row: int, col: int) -> None:
        """Remove obsolete edits when a revealed cell becomes permanently fixed."""
        def keep(move):
            return not isinstance(move, Move) or (move.row, move.col) != (row, col)
        self._undo = [move for move in self._undo if keep(move)]
        self._redo = [move for move in self._redo if keep(move)]

    def clear(self) -> None:
        """Discard all history (e.g., on new game)."""
        self._undo.clear()
        self._redo.clear()
