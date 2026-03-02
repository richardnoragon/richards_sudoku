"""Candidate computation service for Sudoku cells."""
from __future__ import annotations

from richards_sudoku.model.types import Board, VariantMetadata
from richards_sudoku.solver.solver import _build_peer_cache, _candidates


def compute_candidates(
    board: Board,
    row: int,
    col: int,
    variant_meta: VariantMetadata,
) -> set[int]:
    """Return the set of valid candidates for a single empty cell.

    Returns an empty set if the cell already has a value.
    """
    cell = board.cell(row, col)
    if cell.value is not None:
        return set()

    grid = [[board.cell(r, c).value for c in range(board.size)] for r in range(board.size)]
    peer_cache = _build_peer_cache(board.size, variant_meta.region_layout)
    return _candidates(grid, row, col, set(variant_meta.symbols), peer_cache)


def update_all_candidates(board: Board, variant_meta: VariantMetadata) -> None:
    """Recompute and store candidates for every empty, non-fixed cell in-place."""
    grid = [[board.cell(r, c).value for c in range(board.size)] for r in range(board.size)]
    peer_cache = _build_peer_cache(board.size, variant_meta.region_layout)
    symbols = set(variant_meta.symbols)

    for r in range(board.size):
        for c in range(board.size):
            cell = board.cell(r, c)
            if cell.value is None and not cell.is_fixed:
                cell.candidates = _candidates(grid, r, c, symbols, peer_cache)
            elif cell.value is not None:
                cell.candidates = set()
