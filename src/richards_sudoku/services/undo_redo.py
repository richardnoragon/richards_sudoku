"""Undo/redo stack service.

Only board value changes and pencil-mark changes are tracked.
Timer state and hint counters are intentionally excluded.
"""
from __future__ import annotations

from richards_sudoku.model.types import Board, Move


class UndoRedoStack:
    """Manages undo and redo stacks for board and pencil-mark moves."""

    def __init__(self) -> None:
        self._undo: list[Move] = []
        self._redo: list[Move] = []

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

    def push(self, move: Move) -> None:
        """Record a new move and clear the redo stack."""
        self._undo.append(move)
        self._redo.clear()

    def undo(self, board: Board) -> Move | None:
        """Reverse the most recent move on *board* and return it, or None."""
        if not self._undo:
            return None
        move = self._undo.pop()
        board.reverse_move(move)
        self._redo.append(move)
        return move

    def redo(self, board: Board) -> Move | None:
        """Re-apply the most recently undone move on *board* and return it, or None."""
        if not self._redo:
            return None
        move = self._redo.pop()
        board.apply_move(move)
        self._undo.append(move)
        return move

    def clear(self) -> None:
        """Discard all history (e.g., on new game)."""
        self._undo.clear()
        self._redo.clear()
