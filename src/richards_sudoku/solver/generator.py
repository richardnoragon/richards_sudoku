"""Seedable puzzle generator for Sudoku variants.

Generates a fully-filled solution grid, then removes clues while
ensuring the remaining puzzle has a unique solution.
"""
from __future__ import annotations

import random
from typing import Sequence

from richards_sudoku.solver.solver import Grid, _build_peer_cache, _candidates, validate


# ---------------------------------------------------------------------------
# Full-grid generator
# ---------------------------------------------------------------------------

def _fill_grid(
    grid: Grid,
    empties: list[tuple[int, int]],
    idx: int,
    symbols: list[int],
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]],
    rng: random.Random,
) -> bool:
    """Fill *grid* with a valid complete solution using randomised backtracking."""
    if idx == len(empties):
        return True

    row, col = empties[idx]
    cands = list(_candidates(grid, row, col, symbols, peer_cache))
    rng.shuffle(cands)
    for val in cands:
        grid[row][col] = val
        if _fill_grid(grid, empties, idx + 1, symbols, peer_cache, rng):
            return True
        grid[row][col] = None
    return False


def generate_solution(
    size: int,
    region_layout: Sequence[Sequence[int]],
    symbols: list[int],
    seed: int | None = None,
) -> Grid:
    """Return a randomly-filled, valid, complete grid.

    Args:
        size: board dimension.
        region_layout: size×size mapping (row,col) -> region_id.
        symbols: allowed fill values.
        seed: RNG seed for reproducibility; None for random.

    Raises:
        RuntimeError: if filling fails (should not happen for valid metadata).
    """
    rng = random.Random(seed)
    peer_cache = _build_peer_cache(size, region_layout)
    grid: Grid = [[None] * size for _ in range(size)]
    empties = [(r, c) for r in range(size) for c in range(size)]
    if not _fill_grid(grid, empties, 0, symbols, peer_cache, rng):
        raise RuntimeError("Failed to generate a solution grid – check variant metadata.")
    return grid


# ---------------------------------------------------------------------------
# Puzzle generator  (solution → unique puzzle by removing clues)
# ---------------------------------------------------------------------------

def _count_solutions(
    grid: Grid,
    empties: list[tuple[int, int]],
    idx: int,
    symbols: list[int],
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]],
) -> int:
    """Count solutions up to 2 (sufficient to check uniqueness)."""
    if idx == len(empties):
        return 1
    row, col = empties[idx]
    if grid[row][col] is not None:
        return _count_solutions(grid, empties, idx + 1, symbols, peer_cache)
    total = 0
    for val in _candidates(grid, row, col, symbols, peer_cache):
        grid[row][col] = val
        total += _count_solutions(grid, empties, idx + 1, symbols, peer_cache)
        grid[row][col] = None
        if total >= 2:
            break
    return total


def _has_unique_solution(
    grid: Grid,
    size: int,
    symbols: list[int],
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]],
) -> bool:
    empties = [(r, c) for r in range(size) for c in range(size) if grid[r][c] is None]
    return _count_solutions(grid, empties, 0, symbols, peer_cache) == 1


# Approximate target givens per difficulty for 9×9
_DIFFICULTY_GIVENS: dict[str, int] = {
    "easy": 40,
    "medium": 32,
    "hard": 27,
    "expert": 23,
}


def generate_puzzle(
    size: int,
    region_layout: Sequence[Sequence[int]],
    symbols: list[int],
    seed: int | None = None,
    difficulty: str = "medium",
) -> tuple[Grid, Grid]:
    """Generate a Sudoku puzzle together with its solution.

    Args:
        size: board dimension.
        region_layout: size×size mapping (row,col) -> region_id.
        symbols: allowed fill values.
        seed: RNG seed for reproducibility.
        difficulty: one of 'easy', 'medium', 'hard', 'expert'.

    Returns:
        (puzzle, solution) where puzzle has None for empty cells and
        solution is the fully-filled grid.

    Raises:
        ValueError: for unrecognised difficulty.
    """
    if difficulty not in _DIFFICULTY_GIVENS:
        raise ValueError(
            f"Unknown difficulty {difficulty!r}. "
            f"Choose from {list(_DIFFICULTY_GIVENS)}."
        )

    rng = random.Random(seed)
    solution = generate_solution(size, region_layout, symbols, seed=seed)
    peer_cache = _build_peer_cache(size, region_layout)
    target_givens = _DIFFICULTY_GIVENS[difficulty]

    # Start from the full solution; remove cells one at a time
    puzzle: Grid = [row[:] for row in solution]
    all_cells = [(r, c) for r in range(size) for c in range(size)]
    rng.shuffle(all_cells)

    filled = size * size
    for row, col in all_cells:
        if filled <= target_givens:
            break
        saved = puzzle[row][col]
        puzzle[row][col] = None
        if _has_unique_solution(puzzle, size, symbols, peer_cache):
            filled -= 1
        else:
            puzzle[row][col] = saved  # restore – removal broke uniqueness

    return puzzle, solution
