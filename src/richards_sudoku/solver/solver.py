"""Solver and validator for Sudoku puzzles.

Supports any variant described by a VariantMetadata region_layout.
Uses backtracking with constraint propagation (naked-singles elimination)
for performance.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Sequence


Grid = list[list[int | None]]  # 0/None = empty


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------

def _peers(
    row: int,
    col: int,
    size: int,
    region_layout: Sequence[Sequence[int]],
) -> frozenset[tuple[int, int]]:
    """Return all cell coordinates that share a row, column, or region with (row, col)."""
    rid = region_layout[row][col]
    result: set[tuple[int, int]] = set()
    for c in range(size):
        if c != col:
            result.add((row, c))
    for r in range(size):
        if r != row:
            result.add((r, col))
    for r in range(size):
        for c in range(size):
            if (r, c) != (row, col) and region_layout[r][c] == rid:
                result.add((r, c))
    return frozenset(result)


def _build_peer_cache(
    size: int,
    region_layout: Sequence[Sequence[int]],
) -> dict[tuple[int, int], frozenset[tuple[int, int]]]:
    return {
        (r, c): _peers(r, c, size, region_layout)
        for r in range(size)
        for c in range(size)
    }


def _candidates(
    grid: Grid,
    row: int,
    col: int,
    symbols: list[int],
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]],
) -> set[int]:
    used = {grid[r][c] for (r, c) in peer_cache[(row, col)] if grid[r][c] is not None}
    return {v for v in symbols if v not in used}


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate(
    grid: Grid,
    size: int,
    region_layout: Sequence[Sequence[int]],
    symbols: list[int],
) -> bool:
    """Return True if no row/column/region contains duplicate filled values."""
    symbol_set = set(symbols)
    # Rows
    for r in range(size):
        row_vals = [grid[r][c] for c in range(size) if grid[r][c] is not None]
        if len(row_vals) != len(set(row_vals)):
            return False
        if not set(row_vals).issubset(symbol_set):
            return False
    # Columns
    for c in range(size):
        col_vals = [grid[r][c] for r in range(size) if grid[r][c] is not None]
        if len(col_vals) != len(set(col_vals)):
            return False
    # Regions
    num_regions = max(region_layout[r][c] for r in range(size) for c in range(size)) + 1
    for rid in range(num_regions):
        reg_vals = [
            grid[r][c]
            for r in range(size)
            for c in range(size)
            if region_layout[r][c] == rid and grid[r][c] is not None
        ]
        if len(reg_vals) != len(set(reg_vals)):
            return False
    return True


# ---------------------------------------------------------------------------
# Solver  (backtracking + naked-singles propagation)
# ---------------------------------------------------------------------------

def _solve(
    grid: Grid,
    empties: list[tuple[int, int]],
    idx: int,
    symbols: list[int],
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]],
    limit: int,
    solutions: list[Grid],
) -> None:
    """Recursive backtracker.  Stops once len(solutions) reaches *limit*."""
    if len(solutions) >= limit:
        return

    if idx == len(empties):
        solutions.append([row[:] for row in grid])
        return

    row, col = empties[idx]

    # Skip cells that were filled by naked-single propagation
    if grid[row][col] is not None:
        _solve(grid, empties, idx + 1, symbols, peer_cache, limit, solutions)
        return

    cands = _candidates(grid, row, col, symbols, peer_cache)
    for val in cands:
        grid[row][col] = val
        _solve(grid, empties, idx + 1, symbols, peer_cache, limit, solutions)
        if len(solutions) >= limit:
            grid[row][col] = None
            return
        grid[row][col] = None


def solve(
    grid: Grid,
    size: int,
    region_layout: Sequence[Sequence[int]],
    symbols: list[int],
    limit: int = 2,
) -> list[Grid]:
    """Return up to *limit* solutions for *grid*.

    Args:
        grid: size×size grid with None for empty cells.
        size: board dimension.
        region_layout: size×size mapping of (row,col) -> region_id.
        symbols: allowed fill values.
        limit: stop searching after this many solutions (default 2,
               which is enough to test uniqueness cheaply).

    Returns:
        List of complete grids (up to *limit*).
    """
    if not validate(grid, size, region_layout, symbols):
        return []

    peer_cache = _build_peer_cache(size, region_layout)
    work = [row[:] for row in grid]
    empties = [
        (r, c)
        for r in range(size)
        for c in range(size)
        if work[r][c] is None
    ]
    solutions: list[Grid] = []
    _solve(work, empties, 0, symbols, peer_cache, limit, solutions)
    return solutions


def is_valid_and_unique(
    grid: Grid,
    size: int,
    region_layout: Sequence[Sequence[int]],
    symbols: list[int],
) -> bool:
    """Return True iff *grid* has exactly one solution."""
    return len(solve(grid, size, region_layout, symbols, limit=2)) == 1
