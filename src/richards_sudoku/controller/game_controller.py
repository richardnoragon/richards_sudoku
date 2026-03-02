"""GameController — wires all game services into a single callable facade.

Responsibilities
----------------
* Start / reset a new standard game (generate puzzle, bind to grid).
* Apply value edits and pencil-mark toggles, recording undo moves and
  updating stats.
* Undo / redo via the UndoRedoStack.
* Reveal a hint (fills one empty cell from the solution).
* Save and load game state via the persistence layer, restoring board,
  timer, stats and candidate sets.
* Expose state queries the UI needs: can_undo, can_redo, is_complete.
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import TYPE_CHECKING

from richards_sudoku.model.types import Board, Move, Variant, VariantMetadata
from richards_sudoku.persistence.persistence import SaveState, load, save
from richards_sudoku.services.candidates import update_all_candidates
from richards_sudoku.services.stats import GameStats
from richards_sudoku.services.timer import GameTimer
from richards_sudoku.services.undo_redo import UndoRedoStack
from richards_sudoku.solver.generator import generate_puzzle
from richards_sudoku.solver.solver import Grid

if TYPE_CHECKING:
    from richards_sudoku.ui.grid_widget import SudokuGridWidget


class GameController:
    """Facade connecting the UI grid to all backend services.

    Parameters
    ----------
    grid:
        The SudokuGridWidget whose signals this controller subscribes to
        and whose board/meta it keeps updated.
    """

    def __init__(self, grid: "SudokuGridWidget") -> None:
        self._grid = grid
        self._board: Board | None = None
        self._meta: VariantMetadata | None = None
        self._solution: Grid | None = None
        self._undo_stack = UndoRedoStack()
        self._timer = GameTimer()
        self._stats = GameStats()
        self._save_path: Path | None = None

        # Subscribe to grid signals
        grid.value_entered.connect(self._on_value_entered)
        grid.pencil_toggled.connect(self._on_pencil_toggled)

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        return self._undo_stack.can_undo

    @property
    def can_redo(self) -> bool:
        return self._undo_stack.can_redo

    @property
    def is_complete(self) -> bool:
        """True when every cell is filled and there are no conflicts."""
        if self._board is None or self._meta is None:
            return False
        for r in range(self._board.size):
            for c in range(self._board.size):
                if self._board.cell(r, c).value is None:
                    return False
        from richards_sudoku.solver.solver import validate
        grid = [[self._board.cell(r, c).value for c in range(self._board.size)]
                for r in range(self._board.size)]
        return validate(grid, self._board.size,
                        self._meta.region_layout, self._meta.symbols)

    @property
    def elapsed_seconds(self) -> float:
        return self._timer.elapsed_seconds()

    @property
    def stats(self) -> GameStats:
        return self._stats

    @property
    def save_path(self) -> Path | None:
        return self._save_path

    # ------------------------------------------------------------------
    # New game
    # ------------------------------------------------------------------

    def new_game(self, difficulty: str = "medium", seed: int | None = None) -> None:
        """Generate a new standard 9×9 puzzle and bind it to the grid."""
        meta = VariantMetadata.standard_9x9()
        if seed is None:
            seed = random.randrange(2 ** 31)

        puzzle, solution = generate_puzzle(
            size=meta.size,
            region_layout=meta.region_layout,
            symbols=meta.symbols,
            seed=seed,
            difficulty=difficulty,
        )

        board = Board(size=meta.size, variant=Variant.STANDARD)
        for r in range(meta.size):
            for c in range(meta.size):
                v = puzzle[r][c]
                cell = board.cell(r, c)
                if v is not None:
                    cell.value = v
                    cell.is_fixed = True
                    cell.region_id = meta.region_layout[r][c]
                else:
                    cell.region_id = meta.region_layout[r][c]

        update_all_candidates(board, meta)

        self._board = board
        self._meta = meta
        self._solution = solution
        self._undo_stack.clear()
        self._timer.reset()
        self._timer.start()
        self._stats = GameStats()
        self._save_path = None

        self._grid.set_board(board, meta)

    # ------------------------------------------------------------------
    # Edit handlers (connected to grid signals)
    # ------------------------------------------------------------------

    def _on_value_entered(self, row: int, col: int, value: int) -> None:
        """Handle a digit key or delete from the grid."""
        if self._board is None or self._meta is None:
            return
        cell = self._board.cell(row, col)
        if cell.is_fixed:
            return

        new_value = value if value != 0 else None
        if cell.value == new_value:
            return  # no-op

        move = Move(
            row=row, col=col,
            old_value=cell.value,
            new_value=new_value,
            old_candidates=frozenset(cell.candidates),
            new_candidates=frozenset(),
        )
        self._board.apply_move(move)
        self._undo_stack.push(move)
        self._stats.record_move()

        update_all_candidates(self._board, self._meta)
        self._grid.refresh()

        if self.is_complete:
            self._timer.pause()
            self._stats.set_completion_time(self._timer.elapsed_seconds())

    def _on_pencil_toggled(self, row: int, col: int, value: int) -> None:
        """Handle a pencil-mark toggle from the grid."""
        if self._board is None or self._meta is None:
            return
        cell = self._board.cell(row, col)
        if cell.is_fixed or cell.value is not None:
            return

        old_cands = frozenset(cell.candidates)
        new_cands = old_cands.symmetric_difference({value})

        move = Move(
            row=row, col=col,
            old_value=None, new_value=None,
            old_candidates=old_cands,
            new_candidates=new_cands,
        )
        self._board.apply_move(move)
        self._undo_stack.push(move)
        self._stats.record_move()
        self._grid.refresh()

    # ------------------------------------------------------------------
    # Undo / redo
    # ------------------------------------------------------------------

    def undo(self) -> bool:
        """Undo the last move.  Returns True if a move was undone."""
        if self._board is None:
            return False
        move = self._undo_stack.undo(self._board)
        if move is not None:
            if self._meta:
                update_all_candidates(self._board, self._meta)
            self._grid.refresh()
            return True
        return False

    def redo(self) -> bool:
        """Redo the last undone move.  Returns True if a move was redone."""
        if self._board is None:
            return False
        move = self._undo_stack.redo(self._board)
        if move is not None:
            if self._meta:
                update_all_candidates(self._board, self._meta)
            self._grid.refresh()
            return True
        return False

    # ------------------------------------------------------------------
    # Hint
    # ------------------------------------------------------------------

    def hint(self) -> bool:
        """Reveal one empty cell from the solution.  Returns True if applied."""
        if self._board is None or self._meta is None or self._solution is None:
            return False

        # Collect unfilled, non-fixed cells
        empty = [
            (r, c)
            for r in range(self._board.size)
            for c in range(self._board.size)
            if self._board.cell(r, c).value is None and not self._board.cell(r, c).is_fixed
        ]
        if not empty:
            return False

        row, col = random.choice(empty)
        sol_value = self._solution[row][col]
        if sol_value is None:
            return False

        cell = self._board.cell(row, col)
        move = Move(
            row=row, col=col,
            old_value=None, new_value=sol_value,
            old_candidates=frozenset(cell.candidates),
            new_candidates=frozenset(),
        )
        self._board.apply_move(move)
        # Hint moves are NOT pushed to undo stack (per spec)
        self._stats.record_hint()

        update_all_candidates(self._board, self._meta)
        self._grid.refresh()

        if self.is_complete:
            self._timer.pause()
            self._stats.set_completion_time(self._timer.elapsed_seconds())

        return True

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_game(self, path: str | os.PathLike | None = None) -> Path:
        """Save the current game state to *path* (or the last-used path).

        Returns the path written to.
        Raises ValueError if no path is given and none was previously set.
        """
        if path is None:
            if self._save_path is None:
                raise ValueError("No save path specified.")
            path = self._save_path

        if self._board is None or self._meta is None:
            raise ValueError("No active game to save.")

        self._timer.pause()
        state = SaveState(
            board=self._board.copy(),
            variant_meta=self._meta,
            solution=self._solution,
            timer=self._timer,
            stats=self._stats,
        )
        save(state, path)
        self._save_path = Path(path)
        self._timer.resume()
        return self._save_path

    def load_game(self, path: str | os.PathLike) -> None:
        """Load game state from *path* and bind it to the grid."""
        state = load(path)

        self._board = state.board
        self._meta = state.variant_meta
        self._solution = state.solution
        self._timer = state.timer
        self._stats = state.stats
        self._save_path = Path(path)

        self._undo_stack.clear()
        update_all_candidates(self._board, self._meta)
        self._grid.set_board(self._board, self._meta)
        self._timer.resume()
