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
from richards_sudoku.services.difficulty_se import grade as _grade_se
from richards_sudoku.services.variant_registry import REGISTRY
from richards_sudoku.solver.generator import GenerationCancelled, generate_puzzle
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
        self._puzzle_grid: Grid | None = None  # original puzzle for restart
        self._undo_stack = UndoRedoStack()
        self._timer = GameTimer()
        self._stats = GameStats()
        self._save_path: Path | None = None
        self._se_rating: tuple[float, str] = (0.0, "Unknown")
        self._hint_limit: int | None = 3
        self._hints_remaining: int | None = 3
        self._on_complete_callback = None

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
        """True when every non-black cell is filled, no conflicts, and Killer sums match."""
        if self._board is None or self._meta is None:
            return False
        for r in range(self._board.size):
            for c in range(self._board.size):
                cell = self._board.cell(r, c)
                if not cell.is_black and cell.value is None:
                    return False
        if self._has_conflicts():
            return False
        # H4: Killer cage sum check
        if self._meta.name == Variant.KILLER:
            cages = self._meta.constraints.get("cages", []) or []
            for cage in cages:
                target = cage.get("sum")
                if target is None:
                    continue
                total = sum(
                    self._board.cell(int(p[0]), int(p[1])).value or 0
                    for p in cage.get("cells", [])
                )
                if total != target:
                    return False
        # M6: KenKen cage arithmetic check
        if self._meta.name == Variant.KENKEN:
            cages = self._meta.constraints.get("cages", []) or []
            for cage in cages:
                target = cage.get("target")
                op = cage.get("op")
                if target is None or op is None:
                    continue
                vals = [
                    self._board.cell(int(p[0]), int(p[1])).value
                    for p in cage.get("cells", [])
                ]
                if None in vals:
                    return False
                if op == "+":
                    result = sum(vals)  # type: ignore[arg-type]
                elif op == "*":
                    result = 1
                    for v in vals:
                        result *= v  # type: ignore[operator]
                elif op == "-":
                    result = max(vals) - min(vals)  # type: ignore[type-var]
                elif op == "/":
                    mx, mn = max(vals), min(vals)  # type: ignore[type-var]
                    result = mx // mn if mn != 0 else 0  # type: ignore[operator]
                else:
                    continue
                if result != target:
                    return False
        # N6: Kakuro run-sum and no-repeat check
        if self._meta.name == Variant.KAKURO:
            clues = self._meta.constraints.get("clues", []) or []
            for run in clues:
                cells = [(int(p[0]), int(p[1])) for p in run.get("cells", [])]
                target = run.get("sum")
                if target is None:
                    continue
                vals = [self._board.cell(r, c).value for r, c in cells]
                if None in vals:
                    return False
                if sum(vals) != int(target):  # type: ignore[arg-type]
                    return False
                if len(set(vals)) != len(vals):  # type: ignore[arg-type]
                    return False
        return True

    @property
    def hints_remaining(self) -> int | None:
        """Hints left this game, or None for unlimited."""
        return self._hints_remaining

    @property
    def se_rating(self) -> tuple[float, str]:
        """(score, label) from the SukakuExplainer grader for the current puzzle."""
        return self._se_rating

    @property
    def elapsed_seconds(self) -> float:
        return self._timer.elapsed_seconds()

    @property
    def stats(self) -> GameStats:
        return self._stats

    @property
    def save_path(self) -> Path | None:
        return self._save_path

    @property
    def variant_meta(self):
        """The VariantMetadata for the current game, or None."""
        return self._meta

    # ------------------------------------------------------------------
    # New game
    # ------------------------------------------------------------------

    def new_game(
        self,
        meta: VariantMetadata | None = None,
        difficulty: str = "medium",
        seed: int | None = None,
        hint_limit: int | None = 3,
    ) -> None:
        """Generate a new puzzle from *meta* and bind it to the grid.

        If *meta* is None a standard 9×9 game is started (backwards compat).
        """
        if meta is None:
            meta = VariantMetadata.standard_9x9()
        if seed is None:
            seed = random.randrange(2 ** 31)

        # Variant-specific constraint function from the registry
        reg = REGISTRY.get(meta.name, {})
        constraint_ok = reg.get("constraint_ok")
        cancel_flag: list[bool] = [False]

        puzzle, solution = generate_puzzle(
            size=meta.size,
            region_layout=meta.region_layout,
            symbols=meta.symbols,
            seed=seed,
            difficulty=difficulty,
            meta=meta,
            constraint_ok=constraint_ok,
            cancel_flag=cancel_flag,
        )

        # Black cells for Str8ts
        black_cells: set[tuple[int, int]] = set()
        if meta.constraints:
            for p in meta.constraints.get("black_cells", []):
                black_cells.add((int(p[0]), int(p[1])))

        board = Board(size=meta.size, variant=meta.name)
        for r in range(meta.size):
            for c in range(meta.size):
                cell = board.cell(r, c)
                cell.region_id = meta.region_layout[r][c]
                if (r, c) in black_cells:
                    cell.is_black = True
                v = puzzle[r][c]
                if v is not None:
                    cell.value = v
                    cell.is_fixed = True

        update_all_candidates(board, meta)

        self._board = board
        self._meta = meta
        self._solution = solution
        self._puzzle_grid = puzzle
        self._hint_limit = hint_limit
        self._hints_remaining = hint_limit
        self._undo_stack.clear()
        self._timer.reset()
        self._timer.start()
        self._stats = GameStats()
        self._save_path = None

        self._grid.set_board(board, meta)
        self._se_rating = _grade_se(board, meta)

    # ------------------------------------------------------------------
    # Edit handlers (connected to grid signals)
    # ------------------------------------------------------------------

    def _on_value_entered(self, row: int, col: int, value: int) -> None:
        """Handle a digit key or delete from the grid."""
        if self._board is None or self._meta is None:
            return
        cell = self._board.cell(row, col)
        if cell.is_fixed or cell.is_black:  # H3
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
            if self._on_complete_callback is not None:
                self._on_complete_callback()

    def _on_pencil_toggled(self, row: int, col: int, value: int) -> None:
        """Handle a pencil-mark toggle from the grid."""
        if self._board is None or self._meta is None:
            return
        cell = self._board.cell(row, col)
        if cell.is_fixed or cell.is_black or cell.value is not None:  # H3
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

    def hint(self, mode: str = "auto_fill") -> bool:
        """Reveal a hint.  Returns True if a hint was applied.

        Parameters
        ----------
        mode:
            "auto_fill"    – fill a random empty cell from the solution.
            "reveal_cell"  – fill the currently selected cell.
            "eliminate"    – remove one wrong candidate from the selected cell.
            "naked_single" – fill every cell that has exactly one candidate.
        """
        if self._board is None or self._meta is None or self._solution is None:
            return False

        # show_candidate is advisory: never checks or decrements the hint counter.
        if mode == "show_candidate":
            return self._hint_show_candidate()

        if self._hints_remaining is not None and self._hints_remaining <= 0:
            return False

        if mode == "auto_fill":
            applied = self._hint_auto_fill()
        elif mode == "reveal_cell":
            applied = self._hint_reveal_cell()
        elif mode == "eliminate":
            applied = self._hint_eliminate()
        elif mode == "naked_single":
            applied = self._hint_naked_single()
        else:
            applied = self._hint_auto_fill()

        if applied:
            self._stats.record_hint()
            if self._hints_remaining is not None:
                self._hints_remaining -= 1
            if self.is_complete:
                self._timer.pause()
                self._stats.set_completion_time(self._timer.elapsed_seconds())
                if self._on_complete_callback is not None:
                    self._on_complete_callback()
        return applied

    def _hint_auto_fill(self) -> bool:
        """Fill a random empty non-black cell from the solution."""
        empty = [
            (r, c)
            for r in range(self._board.size)
            for c in range(self._board.size)
            if (
                self._board.cell(r, c).value is None
                and not self._board.cell(r, c).is_fixed
                and not self._board.cell(r, c).is_black
            )
        ]
        if not empty:
            return False
        row, col = random.choice(empty)
        return self._apply_hint_fill(row, col)

    def _hint_reveal_cell(self) -> bool:
        """Fill the currently selected cell from the solution."""
        sel = self._grid.selected_cell
        if sel is None:
            return self._hint_auto_fill()
        row, col = sel
        cell = self._board.cell(row, col)
        if cell.value is not None or cell.is_fixed or cell.is_black:
            return False
        return self._apply_hint_fill(row, col)

    def _hint_eliminate(self) -> bool:
        """Remove one wrong candidate from the selected cell."""
        sel = self._grid.selected_cell
        if sel is None:
            return False
        row, col = sel
        cell = self._board.cell(row, col)
        if cell.value is not None or cell.is_black:
            return False
        sol_val = self._solution[row][col]
        if sol_val is None:
            return False
        wrong = cell.candidates - {sol_val}
        if not wrong:
            return False
        to_remove = min(wrong)  # deterministic: lowest wrong candidate
        old_cands = frozenset(cell.candidates)
        new_cands = old_cands - {to_remove}
        move = Move(
            row=row, col=col,
            old_value=None, new_value=None,
            old_candidates=old_cands,
            new_candidates=new_cands,
        )
        self._board.apply_move(move)
        self._undo_stack.push(move)
        update_all_candidates(self._board, self._meta)
        self._grid.refresh()
        return True

    def _hint_naked_single(self) -> bool:
        """Fill all cells that have exactly one candidate."""
        applied = False
        for r in range(self._board.size):
            for c in range(self._board.size):
                cell = self._board.cell(r, c)
                if (
                    cell.value is None
                    and not cell.is_fixed
                    and not cell.is_black
                    and len(cell.candidates) == 1
                ):
                    if self._apply_hint_fill(r, c):
                        applied = True
        return applied

    def _hint_show_candidate(self) -> bool:
        """Reveal the solution candidate for the selected cell.

        Does not fill the cell and does not decrement the hint counter.
        Returns True if the candidate was revealed (or was already visible),
        False if no cell is selected or the cell already has a value.
        """
        if self._board is None or self._solution is None:
            return False
        sel = self._grid.selected_cell
        if sel is None:
            return False
        row, col = sel
        cell = self._board.cell(row, col)
        if cell.value is not None or cell.is_black:
            return False
        sol_val = self._solution[row][col]
        if sol_val is None:
            return False
        if sol_val in cell.candidates:
            return True  # already visible, nothing to change
        old_cands = frozenset(cell.candidates)
        new_cands = old_cands | {sol_val}
        move = Move(
            row=row, col=col,
            old_value=None, new_value=None,
            old_candidates=old_cands,
            new_candidates=new_cands,
        )
        self._board.apply_move(move)
        self._grid.refresh()
        return True

    def _apply_hint_fill(self, row: int, col: int) -> bool:
        """Fill a single cell from the solution (no undo, no stats bookkeeping)."""
        sol_value = self._solution[row][col]
        if sol_value is None:
            return False
        cell = self._board.cell(row, col)
        move = Move(
            row=row, col=col,
            old_value=cell.value, new_value=sol_value,
            old_candidates=frozenset(cell.candidates),
            new_candidates=frozenset(),
        )
        self._board.apply_move(move)
        cell.is_fixed = True  # hint-filled cells become fixed
        update_all_candidates(self._board, self._meta)
        self._grid.refresh()
        return True

    # ------------------------------------------------------------------
    # Completion callback / restart
    # ------------------------------------------------------------------

    def set_complete_callback(self, callback) -> None:
        """Register a callable to invoke when the puzzle is completed."""
        self._on_complete_callback = callback

    def restart_game(self, reset_timer: bool = True) -> None:
        """Reset the board to its original puzzle state."""
        if self._board is None or self._meta is None or self._puzzle_grid is None:
            return

        black_cells: set[tuple[int, int]] = set()
        if self._meta.constraints:
            for p in self._meta.constraints.get("black_cells", []):
                black_cells.add((int(p[0]), int(p[1])))

        board = Board(size=self._meta.size, variant=self._meta.name)
        puzzle = self._puzzle_grid
        for r in range(self._meta.size):
            for c in range(self._meta.size):
                cell = board.cell(r, c)
                cell.region_id = self._meta.region_layout[r][c]
                if (r, c) in black_cells:
                    cell.is_black = True
                v = puzzle[r][c]
                if v is not None:
                    cell.value = v
                    cell.is_fixed = True

        update_all_candidates(board, self._meta)
        self._board = board
        self._undo_stack.clear()
        self._hints_remaining = self._hint_limit
        self._stats = GameStats()
        if reset_timer:
            self._timer.reset()
            self._timer.start()
        self._grid.set_board(board, self._meta)

    def _has_conflicts(self) -> bool:
        """Return True if any two non-black cells in the same unit share a value."""
        board = self._board
        size = board.size
        region_layout = self._meta.region_layout
        num_regions = max(
            region_layout[r][c] for r in range(size) for c in range(size)
        ) + 1
        row_seen: list[dict[int, int]] = [{} for _ in range(size)]
        col_seen: list[dict[int, int]] = [{} for _ in range(size)]
        reg_seen: list[dict[int, int]] = [{} for _ in range(num_regions)]
        for r in range(size):
            for c in range(size):
                cell = board.cell(r, c)
                if cell.is_black or cell.value is None:
                    continue
                v = cell.value
                rid = region_layout[r][c]
                if v in row_seen[r] or v in col_seen[c] or v in reg_seen[rid]:
                    return True
                row_seen[r][v] = 1
                col_seen[c][v] = 1
                reg_seen[rid][v] = 1
        return False

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
            se_score=self._se_rating[0],
            se_label=self._se_rating[1],
            hint_limit=self._hint_limit,
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
        self._hint_limit = state.hint_limit
        self._hints_remaining = state.hint_limit

        self._undo_stack.clear()
        update_all_candidates(self._board, self._meta)
        self._grid.set_board(self._board, self._meta)
        self._se_rating = (state.se_score, state.se_label)
        self._timer.resume()
