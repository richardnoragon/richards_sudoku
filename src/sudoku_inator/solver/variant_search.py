"""Bounded solution counting for variants with cages, runs, or black cells.

An exhausted search returns None, never a claim of uniqueness. Generation keeps
more clues when proof would exceed the budget.
"""
from __future__ import annotations

import random

from sudoku_inator.model.types import Board, VariantMetadata
from sudoku_inator.services.candidates import update_all_candidates
from sudoku_inator.services.validation import conflict_cells


def board_from_values(meta: VariantMetadata, values) -> Board:
    board = Board(meta.size, meta.name)
    black = {tuple(p) for p in meta.constraints.get("black_cells", [])}
    for r in range(meta.size):
        for c in range(meta.size):
            cell = board.cell(r, c)
            cell.value = values[r][c]
            cell.region_id = meta.region_layout[r][c]
            cell.is_black = (r, c) in black
    return board


def count_variant_solutions(meta, values, *, limit=2, max_nodes=1000, cancel_flag=None):
    """Count up to limit valid completions, or return None when interrupted."""
    nodes = 0

    def visit(board):
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes or (cancel_flag is not None and cancel_flag[0]):
            return None
        while True:
            if conflict_cells(board, meta):
                return 0
            update_all_candidates(board, meta)
            empty = [(r, c) for r in range(meta.size) for c in range(meta.size)
                     if not board.cell(r, c).is_black and board.cell(r, c).value is None]
            if not empty:
                return 1
            row, col = min(empty, key=lambda p: len(board.cell(*p).candidates))
            candidates = sorted(board.cell(row, col).candidates)
            if not candidates:
                return 0
            if len(candidates) != 1:
                break
            board.cell(row, col).value = candidates[0]
        total = 0
        for value in candidates:
            trial = board.copy()
            trial.cell(row, col).value = value
            count = visit(trial)
            if count is None:
                return None
            total += count
            if total >= limit:
                return limit
        return total

    return visit(board_from_values(meta, values))


def remove_variant_clues(meta, solution, *, seed, difficulty, cancel_flag=None):
    """Remove clues only when the resulting variant puzzle is proven unique."""
    puzzle = [row[:] for row in solution]
    black = {tuple(p) for p in meta.constraints.get("black_cells", [])}
    cells = [(r, c) for r in range(meta.size) for c in range(meta.size) if (r, c) not in black]
    random.Random(seed).shuffle(cells)
    target = int(len(cells) * {"easy": .5, "medium": .4, "hard": .3, "expert": .25}[difficulty])
    remaining = len(cells)
    for r, c in cells:
        if remaining <= target or (cancel_flag is not None and cancel_flag[0]):
            break
        value = puzzle[r][c]
        puzzle[r][c] = None
        if count_variant_solutions(meta, puzzle, max_nodes=100, cancel_flag=cancel_flag) == 1:
            remaining -= 1
        else:
            puzzle[r][c] = value
    return puzzle
