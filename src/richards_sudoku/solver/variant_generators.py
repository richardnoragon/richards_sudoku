"""Variant-specific layout generators for Jigsaw, Str8ts, Killer, and Kakuro.

All generators are seeded for reproducibility and accept a *cancel_flag*
list (single-element mutable container) to support cooperative cancellation
from a background worker thread.
"""
from __future__ import annotations

import random
from collections import deque
from typing import Any


# ---------------------------------------------------------------------------
# Jigsaw region generator
# ---------------------------------------------------------------------------

class JigsawRegionGenerator:
    """Generate a valid jigsaw region layout for a *size*×*size* board.

    The layout is produced by starting with standard box regions and
    repeatedly swapping random border cell pairs while maintaining
    BFS-connectivity within each region.

    Parameters
    ----------
    size:       board dimension (must be a perfect square, e.g. 9).
    seed:       RNG seed for reproducibility.
    difficulty: 'easy' → fewer swaps (more box-like); 'expert' → more swaps.
    """

    _SWAPS_BY_DIFFICULTY: dict[str, int] = {
        "easy": 20,
        "medium": 60,
        "hard": 120,
        "expert": 200,
    }

    def __init__(self, size: int, seed: int, difficulty: str = "medium") -> None:
        if size < 4:
            raise ValueError("size must be at least 4")
        self._size = size
        self._rng = random.Random(seed)
        sq = int(size ** 0.5)
        self._swaps = self._SWAPS_BY_DIFFICULTY.get(difficulty, 60)
        # Start from standard box layout
        self._layout: list[list[int]] = [
            [(r // sq) * sq + (c // sq) for c in range(size)]
            for r in range(size)
        ]

    def generate(self) -> list[list[int]]:
        """Return a *size*×*size* region layout (region_id per cell)."""
        layout = [row[:] for row in self._layout]
        size = self._size
        swaps_done = 0
        attempts = 0
        max_attempts = self._swaps * 200

        while swaps_done < self._swaps and attempts < max_attempts:
            attempts += 1
            # Identify two neighbouring regions via a random boundary edge
            r = self._rng.randrange(size)
            c = self._rng.randrange(size)
            dr, dc = self._rng.choice([(0, 1), (1, 0)])
            nr, nc = r + dr, c + dc
            if not (0 <= nr < size and 0 <= nc < size):
                continue
            reg_a = layout[r][c]
            reg_b = layout[nr][nc]
            if reg_a == reg_b:
                continue

            # Collect the full shared border between reg_a and reg_b
            side_a: list[tuple[int, int]] = []
            side_b: list[tuple[int, int]] = []
            seen_a: set[tuple[int, int]] = set()
            seen_b: set[tuple[int, int]] = set()
            for row in range(size):
                for col in range(size):
                    reg = layout[row][col]
                    if reg not in (reg_a, reg_b):
                        continue
                    for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nrow, ncol = row + drow, col + dcol
                        if not (0 <= nrow < size and 0 <= ncol < size):
                            continue
                        nreg = layout[nrow][ncol]
                        if reg == reg_a and nreg == reg_b:
                            if (row, col) not in seen_a:
                                side_a.append((row, col))
                                seen_a.add((row, col))
                        elif reg == reg_b and nreg == reg_a:
                            if (row, col) not in seen_b:
                                side_b.append((row, col))
                                seen_b.add((row, col))

            if not side_a or not side_b:
                continue

            # Prefer a non-adjacent pair so each cell retains a neighbour in
            # its new region and avoids becoming isolated.
            self._rng.shuffle(side_a)
            self._rng.shuffle(side_b)
            cell_a: tuple[int, int] | None = None
            cell_b: tuple[int, int] | None = None
            for ca in side_a:
                for cb in side_b:
                    if abs(ca[0] - cb[0]) + abs(ca[1] - cb[1]) > 1:
                        cell_a, cell_b = ca, cb
                        break
                if cell_a is not None:
                    break
            if cell_a is None:
                # All pairs are adjacent; let the connectivity check decide
                cell_a, cell_b = side_a[0], side_b[0]

            ar, ac = cell_a
            br, bc = cell_b
            layout[ar][ac] = reg_b
            layout[br][bc] = reg_a
            if self._is_connected(layout, reg_a) and self._is_connected(layout, reg_b):
                swaps_done += 1
            else:
                layout[ar][ac] = reg_a
                layout[br][bc] = reg_b

        return layout

    def _is_connected(self, layout: list[list[int]], region_id: int) -> bool:
        """BFS connectivity check for a single region."""
        size = self._size
        cells = [(r, c) for r in range(size) for c in range(size) if layout[r][c] == region_id]
        if not cells:
            return True
        visited: set[tuple[int, int]] = set()
        q: deque[tuple[int, int]] = deque([cells[0]])
        visited.add(cells[0])
        cell_set = set(cells)
        while q:
            r, c = q.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb not in visited and nb in cell_set:
                    visited.add(nb)
                    q.append(nb)
        return len(visited) == len(cells)


# ---------------------------------------------------------------------------
# Str8ts black-cell mask generator
# ---------------------------------------------------------------------------

class Str8tsMaskGenerator:
    """Generate a point-symmetric black-cell mask for a Str8ts puzzle.

    Black cells are placed with 180° point symmetry around the board centre.
    Density (proportion of black cells) is chosen by difficulty.
    Each resulting white-cell run in every row and column is at least 2 cells.

    Parameters
    ----------
    size:       board dimension (typically 9).
    seed:       RNG seed.
    difficulty: controls target black-cell density.
    """

    _DENSITY_BY_DIFFICULTY: dict[str, float] = {
        "easy": 0.10,
        "medium": 0.15,
        "hard": 0.20,
        "expert": 0.25,
    }

    def __init__(self, size: int, seed: int, difficulty: str = "medium") -> None:
        self._size = size
        self._rng = random.Random(seed)
        self._target_density = self._DENSITY_BY_DIFFICULTY.get(difficulty, 0.22)

    def generate(self) -> set[tuple[int, int]]:
        """Return the set of black (blocked) cell coordinates."""
        size = self._size
        target = int(self._target_density * size * size / 2)  # pairs
        candidates = [
            (r, c)
            for r in range(size)
            for c in range(size)
            if (size - 1 - r, size - 1 - c) > (r, c)  # only upper half of symmetric pairs
        ]
        self._rng.shuffle(candidates)

        blacks: set[tuple[int, int]] = set()
        placed = 0
        for r, c in candidates:
            if placed >= target:
                break
            sym_r, sym_c = size - 1 - r, size - 1 - c
            trial = blacks | {(r, c), (sym_r, sym_c)}
            if self._valid_runs(trial):
                blacks = trial
                placed += 1

        return blacks

    def _valid_runs(self, blacks: set[tuple[int, int]]) -> bool:
        """Ensure every white-cell run in every row and column is >= 2 cells."""
        size = self._size
        for r in range(size):
            run = 0
            for c in range(size):
                if (r, c) in blacks:
                    if 0 < run < 2:
                        return False
                    run = 0
                else:
                    run += 1
            if 0 < run < 2:
                return False
        for c in range(size):
            run = 0
            for r in range(size):
                if (r, c) in blacks:
                    if 0 < run < 2:
                        return False
                    run = 0
                else:
                    run += 1
            if 0 < run < 2:
                return False
        return True


# ---------------------------------------------------------------------------
# Killer cage partitioner
# ---------------------------------------------------------------------------

class CagePartitioner:
    """Partition a solved grid into Killer cages via flood-fill.

    Cages are small contiguous groups of orthogonally adjacent cells.
    Target cage size varies by difficulty: Easy favours large cages (simpler
    sums), Expert favours small ones (harder deduction).

    Parameters
    ----------
    size:        board dimension.
    seed:        RNG seed (same seed as solution fill for reproducibility).
    rng:         optional shared ``random.Random`` instance; if given, *seed*
                 is ignored.
    """

    _MAX_CAGE_SIZE_BY_DIFFICULTY: dict[str, int] = {
        "easy": 5,
        "medium": 4,
        "hard": 3,
        "expert": 3,
    }

    def __init__(
        self,
        size: int,
        seed: int = 0,
        rng: random.Random | None = None,
        difficulty: str = "medium",
    ) -> None:
        self._size = size
        self._rng = rng if rng is not None else random.Random(seed)
        self._max_cage = self._MAX_CAGE_SIZE_BY_DIFFICULTY.get(difficulty, 4)

    def partition(
        self,
        solution: list[list[int | None]],
        cancel_flag: list[bool] | None = None,
    ) -> list[dict[str, Any]]:
        """Return cage dicts ``{"cells": [[r,c],...], "sum": N}``.

        Checks *cancel_flag* approximately every 100 placements.
        """
        size = self._size
        assigned: list[list[int]] = [[-1] * size for _ in range(size)]
        cages: list[dict[str, Any]] = []
        unassigned = [(r, c) for r in range(size) for c in range(size)]
        self._rng.shuffle(unassigned)

        placements = 0
        for start_r, start_c in unassigned:
            if assigned[start_r][start_c] != -1:
                continue
            if cancel_flag is not None and placements % 100 == 0:
                if cancel_flag[0]:
                    raise _PartitionCancelled()
            # BFS flood fill up to max_cage size
            cage_cells: list[tuple[int, int]] = []
            frontier: deque[tuple[int, int]] = deque([(start_r, start_c)])
            visited: set[tuple[int, int]] = {(start_r, start_c)}
            while frontier and len(cage_cells) < self._max_cage:
                r, c = frontier.popleft()
                if assigned[r][c] != -1:
                    continue
                cage_cells.append((r, c))
                assigned[r][c] = len(cages)
                # Shuffle neighbours so cages are irregular
                neighbours = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
                self._rng.shuffle(neighbours)
                for nr, nc in neighbours:
                    if (
                        0 <= nr < size and 0 <= nc < size
                        and assigned[nr][nc] == -1
                        and (nr, nc) not in visited
                    ):
                        visited.add((nr, nc))
                        frontier.append((nr, nc))
            if cage_cells:
                cage_sum = sum(solution[r][c] for r, c in cage_cells)  # type: ignore[index]
                cages.append({
                    "cells": [[r, c] for r, c in cage_cells],
                    "sum": cage_sum,
                })
                placements += 1

        return cages


class _PartitionCancelled(Exception):
    """Internal exception for cooperative cancellation in CagePartitioner."""


# ---------------------------------------------------------------------------
# 1–25 generator (K1)
# ---------------------------------------------------------------------------

class OneToTwentyFiveGenerator:
    """Generate a valid 25×25 Sudoku solution using band-shuffle technique.

    A cyclic base grid is shuffled by swapping row-bands, rows within bands,
    column-bands, columns within column-bands, and finally symbol labels.
    All operations preserve row/column/box uniqueness guarantees.

    Parameters
    ----------
    size:       must be 25.
    seed:       RNG seed for reproducibility.
    difficulty: accepted for API symmetry; not used during solution generation.
    rng:        optional pre-constructed ``random.Random`` instance to thread
                through multiple generator phases (e.g. from OneToTwentyFiveWorker).
                When supplied, *seed* is ignored for random operations.
    """

    def __init__(
        self,
        size: int = 25,
        seed: int = 0,
        difficulty: str = "medium",
        rng: random.Random | None = None,
    ) -> None:
        if size != 25:
            raise ValueError(f"OneToTwentyFiveGenerator only supports size=25; got {size}")
        self._size = size
        self._box = 5
        self._difficulty = difficulty
        self._rng: random.Random = rng if rng is not None else random.Random(seed)

    def generate(self, cancel_flag: list[bool] | None = None) -> list[list[int]]:
        """Return a valid complete 25×25 solution grid.

        The band-shuffle approach is O(N²) — fast enough that no mid-generation
        cancel checks are required beyond the initial guard below.
        """
        if cancel_flag is not None and cancel_flag[0]:
            return []

        size = self._size
        box = self._box
        rng = self._rng

        # Step 1 — cyclic base: base[r][c] = ((r//box) + (r%box)*box + c) % size + 1
        # Every row, column, and box contains each value exactly once.
        base: list[list[int]] = [
            [((r // box) + (r % box) * box + c) % size + 1 for c in range(size)]
            for r in range(size)
        ]

        # Step 2 — shuffle row-bands (permute which 5-row block comes first)
        row_bands = list(range(box))
        rng.shuffle(row_bands)
        base = [base[bnd * box + i] for bnd in row_bands for i in range(box)]

        # Step 3 — shuffle rows within each band
        for bnd in range(box):
            start = bnd * box
            perm = list(range(start, start + box))
            rng.shuffle(perm)
            tmp = [base[r][:] for r in range(start, start + box)]
            for i in range(box):
                base[start + i] = tmp[perm[i] - start]

        # Step 4 — shuffle column-bands
        col_bands = list(range(box))
        rng.shuffle(col_bands)
        for r in range(size):
            old = base[r]
            base[r] = [old[cb * box + j] for cb in col_bands for j in range(box)]

        # Step 5 — shuffle columns within each column-band
        for cb in range(box):
            start = cb * box
            perm = list(range(start, start + box))
            rng.shuffle(perm)
            for r in range(size):
                old = base[r][:]
                for i in range(box):
                    base[r][start + i] = old[perm[i]]

        # Step 6 — relabel symbols (1–25 permutation)
        symbols = list(range(1, size + 1))
        rng.shuffle(symbols)
        sym = {i + 1: symbols[i] for i in range(size)}
        base = [[sym[v] for v in row] for row in base]

        return base


# ---------------------------------------------------------------------------
# Codewords generator (L1)
# ---------------------------------------------------------------------------

class CodewordsGenerator:
    """Generate a Codewords Sudoku puzzle.

    Codewords is a standard 9×9 Sudoku where the 9 symbols are letters A–I
    instead of digits 1–9.  A ``codebook`` bijection maps letters to digits
    (e.g. ``{"A": 1, "B": 2, ...}``).  A subset of the codebook entries
    (``given_mappings``) are revealed as fixed letter-to-digit clues.

    Generation pipeline (all five steps share a single ``rng`` instance):
    1. Backtracking fill of a standard 9×9 solution (digit layer).
    2. Random bijective codebook: shuffle digits 1–9 and assign to A–I.
    3. Clue removal per difficulty (uses ``_DIFFICULTY_GIVENS``).
    4. ``given_mappings`` selection: reveal a difficulty-tier number of
       letter-to-digit pairs as locked hints.
    5. Digit-layer uniqueness verification via ``_has_unique_solution``.

    Parameters
    ----------
    size:       must be 9.
    seed:       RNG seed for reproducibility.
    difficulty: "easy"|"medium"|"hard"|"expert".
    rng:        optional pre-constructed ``random.Random`` to thread through
                all five pipeline steps.  When provided *seed* is ignored.
    """

    _DIFFICULTY_GIVENS: dict[str, int] = {
        "easy": 40,
        "medium": 32,
        "hard": 27,
        "expert": 23,
    }
    # Number of letter→digit pairs revealed in given_mappings per difficulty
    _GIVEN_MAPPINGS_COUNT: dict[str, int] = {
        "easy": 5,
        "medium": 3,
        "hard": 2,
        "expert": 1,
    }
    _LETTERS: list[str] = list("ABCDEFGHI")

    def __init__(
        self,
        size: int = 9,
        seed: int = 0,
        difficulty: str = "medium",
        rng: random.Random | None = None,
    ) -> None:
        if size != 9:
            raise ValueError(f"CodewordsGenerator only supports size=9; got {size}")
        self._size = size
        self._difficulty = difficulty
        self._rng: random.Random = rng if rng is not None else random.Random(seed)

    def generate(
        self,
        cancel_flag: list[bool] | None = None,
    ) -> dict:
        """Return a dict with keys:
            ``solution``       – 9×9 list[list[int]] (digit layer)
            ``puzzle``         – 9×9 list[list[int|None]] with clues removed
            ``codebook``       – dict mapping letter → digit  (e.g. {"A": 3, ...})
            ``given_mappings`` – dict (subset of codebook) revealed to the player
        Raises ``RuntimeError`` if generation is cancelled.
        """
        from richards_sudoku.solver.generator import (
            generate_solution,
            _has_unique_solution,
        )
        from richards_sudoku.solver.solver import _build_peer_cache

        def _cancelled() -> bool:
            return cancel_flag is not None and cancel_flag[0]

        if _cancelled():
            raise RuntimeError("Cancelled")

        rng = self._rng
        size = self._size

        # Step 1 — fill solution using standard backtracking
        region_layout = [[(r // 3) * 3 + (c // 3) for c in range(9)] for r in range(9)]
        symbols = list(range(1, 10))
        peer_cache = _build_peer_cache(size, region_layout)
        solution = generate_solution(
            size=size,
            region_layout=region_layout,
            symbols=symbols,
            seed=rng.randint(0, 2**31),
        )
        if _cancelled():
            raise RuntimeError("Cancelled")

        # Step 2 — random bijective codebook: letters A–I → digits (shuffled)
        digits = list(range(1, 10))
        rng.shuffle(digits)
        codebook: dict[str, int] = {letter: digit for letter, digit in zip(self._LETTERS, digits)}

        # Step 3 — clue removal
        target_givens = self._DIFFICULTY_GIVENS.get(self._difficulty, 32)
        puzzle = [row[:] for row in solution]
        positions = [(r, c) for r in range(size) for c in range(size)]
        rng.shuffle(positions)
        removed = 0
        for r, c in positions:
            if _cancelled():
                raise RuntimeError("Cancelled")
            if size * size - removed <= target_givens:
                break
            saved = puzzle[r][c]
            puzzle[r][c] = None
            if _has_unique_solution(puzzle, size, symbols, peer_cache):
                removed += 1
            else:
                puzzle[r][c] = saved

        if _cancelled():
            raise RuntimeError("Cancelled")

        # Step 4 — given_mappings selection
        n_reveal = self._GIVEN_MAPPINGS_COUNT.get(self._difficulty, 3)
        letter_order = self._LETTERS[:]
        rng.shuffle(letter_order)
        revealed_letters = letter_order[:n_reveal]
        given_mappings: dict[str, int] = {L: codebook[L] for L in revealed_letters}

        return {
            "solution": solution,
            "puzzle": puzzle,
            "codebook": codebook,
            "given_mappings": given_mappings,
        }


# ---------------------------------------------------------------------------
# KenKen Batch M
# ---------------------------------------------------------------------------

class KenKenCagePartitioner:
    """Seeded flood-fill cage partitioner for an N×N Latin-square solution.

    Produces a full partition of the N×N grid into cages, each cage annotated
    with an arithmetic operation (+, −, ×, ÷) and a target integer.

    Parameters
    ----------
    size:
        Board dimension (typically 4, 6, or 9).
    seed:
        RNG seed for reproducibility.  An internal ``random.Random(seed)``
        instance is created; the *rng* parameter is accepted for interface
        symmetry but not used.
    difficulty:
        "easy" | "medium" | "hard" | "expert".
    rng:
        Ignored — accepted for interface symmetry only.

    Usage
    -----
    ``partitioner.partition(solution) -> list[dict]``

    Each cage dict has the keys:
        ``"cells"``   – list of [row, col] lists covering the cage
        ``"op"``       – one of ``"+"``, ``"-"``, ``"*"``, ``"/"``
        ``"target"``   – integer result of the cage arithmetic

    Single-cell cages always use op ``"+"`` and target == the cell value.

    The caller (KenKenWorker) checks that the number of single-cell cages
    falls within the difficulty-scaled target range and retries with a
    different seed if not.
    """

    # Target average cage sizes per difficulty (flood-fill governed by these)
    _AVG_CAGE_SIZE: dict[str, float] = {
        "easy": 2.5,
        "medium": 3.5,
        "hard": 4.0,
        "expert": 4.5,
    }
    # Scaled single-cell clue target: floor(DIFFICULTY_GIVENS[difficulty] × N² / 81)
    # Mirrors CodewordsGenerator / Killer pattern
    _DIFFICULTY_GIVENS: dict[str, int] = {
        "easy": 40,
        "medium": 32,
        "hard": 27,
        "expert": 23,
    }

    def __init__(
        self,
        size: int,
        seed: int,
        difficulty: str = "medium",
        rng: random.Random | None = None,  # interface symmetry — not used
    ) -> None:
        self._size = size
        self._difficulty = difficulty
        # Create own RNG from seed (rng param is ignored per spec)
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def partition(
        self,
        solution: list[list[int]],
        cancel_flag: list[bool] | None = None,
    ) -> list[dict]:
        """Partition *solution* into cages and return list of cage dicts.

        Raises ``RuntimeError`` if cancelled.
        """
        size = self._size
        rng = self._rng
        avg_size = self._AVG_CAGE_SIZE.get(self._difficulty, 3.5)

        if cancel_flag is not None and cancel_flag[0]:
            raise RuntimeError("Cancelled")

        # --- flood-fill partitioning ---
        assigned: list[list[int | None]] = [[None] * size for _ in range(size)]
        cages_cells: list[list[tuple[int, int]]] = []
        cage_id = 0

        cells = [(r, c) for r in range(size) for c in range(size)]
        rng.shuffle(cells)

        for start_r, start_c in cells:
            if assigned[start_r][start_c] is not None:
                continue
            if cancel_flag is not None and cancel_flag[0]:
                raise RuntimeError("Cancelled")

            # Decide cage size using geometric distribution capped by avg
            desired = self._sample_cage_size(avg_size, rng)
            cage: list[tuple[int, int]] = []
            frontier: list[tuple[int, int]] = []
            cell_set: set[tuple[int, int]] = set()

            # Seed the cage
            cage.append((start_r, start_c))
            cell_set.add((start_r, start_c))
            assigned[start_r][start_c] = cage_id
            self._add_neighbours(start_r, start_c, size, assigned, cell_set, frontier)

            while len(cage) < desired and frontier:
                rng.shuffle(frontier)
                nr, nc = frontier.pop()
                if assigned[nr][nc] is not None:
                    continue
                cage.append((nr, nc))
                cell_set.add((nr, nc))
                assigned[nr][nc] = cage_id
                self._add_neighbours(nr, nc, size, assigned, cell_set, frontier)

            cages_cells.append(cage)
            cage_id += 1

        # --- operation + target assignment ---
        result: list[dict] = []
        for cage in cages_cells:
            values = [solution[r][c] for r, c in cage]
            op, target = self._assign_operation(values, rng)
            result.append({
                "cells": [[r, c] for r, c in cage],
                "op": op,
                "target": target,
            })

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _add_neighbours(
        r: int,
        c: int,
        size: int,
        assigned: list[list[int | None]],
        cell_set: set[tuple[int, int]],
        frontier: list[tuple[int, int]],
    ) -> None:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size:
                if assigned[nr][nc] is None and (nr, nc) not in cell_set:
                    frontier.append((nr, nc))

    @staticmethod
    def _sample_cage_size(avg: float, rng: random.Random) -> int:
        """Sample a cage size with a geometric-ish distribution around *avg*."""
        p = 1.0 / avg
        size = 1
        while rng.random() > p and size < 9:
            size += 1
        return size

    @staticmethod
    def _assign_operation(values: list[int], rng: random.Random) -> tuple[str, int]:
        """Return (op, target) for the given cage *values*."""
        n = len(values)

        if n == 1:
            return "+", values[0]

        if n == 2:
            a, b = values[0], values[1]
            big, small = max(a, b), min(a, b)
            # Eligible operations
            candidates: list[tuple[str, int]] = []
            candidates.append(("+", a + b))
            candidates.append(("-", big - small))
            candidates.append(("*", a * b))
            if small != 0 and big % small == 0:
                candidates.append(("/", big // small))
            op, target = rng.choice(candidates)
            return op, target

        # Multi-cell (3+): only + and * make sense
        if rng.random() < 0.7:  # prefer +
            return "+", sum(values)
        else:
            product = 1
            for v in values:
                product *= v
            return "*", product


# ---------------------------------------------------------------------------
# Kakuro layout generator, fill engine, and clue-position builder
# ---------------------------------------------------------------------------

def _kakuro_run_lengths(r: int, c: int, black: set, size: int) -> tuple[int, int]:
    """Return (across_len, down_len) for the run containing white cell (r, c)."""
    # across: scan left and right
    across = 1
    cc = c - 1
    while cc >= 0 and (r, cc) not in black:
        across += 1
        cc -= 1
    cc = c + 1
    while cc < size and (r, cc) not in black:
        across += 1
        cc += 1
    # down: scan up and down
    down = 1
    rr = r - 1
    while rr >= 0 and (rr, c) not in black:
        down += 1
        rr -= 1
    rr = r + 1
    while rr < size and (rr, c) not in black:
        down += 1
        rr += 1
    return across, down


def _kakuro_extract_runs(white_cells: list, black: set, size: int) -> list[dict]:
    """Extract all horizontal and vertical runs from the template."""
    runs: list[dict] = []
    white_set = set(white_cells)
    # Across runs: left-to-right scan per row
    for r in range(size):
        c = 0
        while c < size:
            if (r, c) in black or (r, c) not in white_set:
                c += 1
                continue
            run_cells = [(r, c)]
            c += 1
            while c < size and (r, c) not in black and (r, c) in white_set:
                run_cells.append((r, c))
                c += 1
            if len(run_cells) >= 2:
                runs.append({"cells": run_cells, "dir": "across"})
    # Down runs: top-to-bottom scan per column
    for c in range(size):
        r = 0
        while r < size:
            if (r, c) in black or (r, c) not in white_set:
                r += 1
                continue
            run_cells = [(r, c)]
            r += 1
            while r < size and (r, c) not in black and (r, c) in white_set:
                run_cells.append((r, c))
                r += 1
            if len(run_cells) >= 2:
                runs.append({"cells": run_cells, "dir": "down"})
    return runs


def build_kakuro_clue_positions(clues: list[dict]) -> dict:
    """Build clue_positions mapping from a list of run dicts with sums.

    Returns a plain dict keyed by ``(row, col)`` tuples where a black/border
    cell carries a clue label.  Values are ``{"across": int, "down": int}``
    dicts (each key present only when that direction has a clue).
    """
    positions: dict = {}
    for run in clues:
        cells = [(int(p[0]), int(p[1])) for p in run["cells"]]
        s = int(run["sum"])
        direction = run["dir"]
        if direction == "across":
            r, c = cells[0]
            key = (r, c - 1)
            positions.setdefault(key, {})["across"] = s
        elif direction == "down":
            r, c = cells[0]
            key = (r - 1, c)
            positions.setdefault(key, {})["down"] = s
    return positions


class KakuroTemplateLibrary:
    """Runtime procedural Kakuro grid-layout generator (no pre-committed files).

    Generates a random black/white cell pattern for a *size*×*size* Kakuro
    board.  Row 0 and column 0 are always black (boundary clue cells).
    Interior cells are randomly assigned, then run-length and connectivity
    constraints are enforced.

    Parameters
    ----------
    size:        Board dimension (typically 9).
    seed:        Base RNG seed.
    difficulty:  Controls the fraction of white (fillable) cells.
    """

    _DENSITY_BANDS: dict[str, tuple[float, float]] = {
        "easy":   (0.50, 0.65),
        "medium": (0.40, 0.55),
        "hard":   (0.30, 0.45),
        "expert": (0.25, 0.40),
    }
    _MAX_ATTEMPTS = 300

    def __init__(self, size: int, seed: int, difficulty: str = "medium") -> None:
        self._size = size
        self._seed = seed
        diff_key = difficulty.lower() if difficulty.lower() in self._DENSITY_BANDS else "medium"
        self._density_lo, self._density_hi = self._DENSITY_BANDS[diff_key]

    def generate(self, cancel_flag: list | None = None) -> dict | None:
        """Return a template dict or *None* on failure/cancellation.

        The returned dict has keys:
        - ``"size"``: int
        - ``"black_cells"``: sorted list of ``[r, c]`` pairs
        - ``"runs"``: list of run dicts (``{"cells": [...], "dir": "across"|"down"}``)
          without sums (sums are derived later from the filled grid).
        """
        size = self._size
        lo, hi = self._density_lo, self._density_hi
        all_interior = [(r, c) for r in range(1, size) for c in range(1, size)]
        n_interior = len(all_interior)

        for attempt in range(self._MAX_ATTEMPTS):
            if cancel_flag is not None and cancel_flag[0]:
                return None

            rng = random.Random(self._seed + attempt)

            # Boundary: row 0 and col 0 are always black
            black: set[tuple[int, int]] = set()
            for i in range(size):
                black.add((0, i))
                black.add((i, 0))

            # Start at a higher initial density so the run-length fixup cascade
            # settles within the target band.  Drawing "start" uniformly from
            # [0.65, 0.80] covers all difficulty bands while avoiding the
            # catastrophic cascade that occurs when starting near the target.
            start_density = rng.uniform(0.65, 0.80)
            n_black_interior = max(0, round(n_interior * (1.0 - start_density)))
            shuffled = all_interior[:]
            rng.shuffle(shuffled)
            for cell in shuffled[:n_black_interior]:
                black.add(cell)

            # Iteratively mark cells black if they're in a run of length < 2
            changed = True
            while changed:
                changed = False
                for r, c in all_interior:
                    if (r, c) in black:
                        continue
                    alen, dlen = _kakuro_run_lengths(r, c, black, size)
                    if alen < 2 or dlen < 2:
                        black.add((r, c))
                        changed = True

            white_cells = [(r, c) for r, c in all_interior if (r, c) not in black]
            if not white_cells:
                continue

            # Check connectivity (all white interior cells reachable from the first)
            if not self._is_connected(white_cells, black, size):
                continue

            # Check density in target band
            density = len(white_cells) / n_interior
            if not (lo <= density <= hi):
                continue

            # Validate max run length (max 9 cells; can't fill with unique 1-9 otherwise)
            runs = _kakuro_extract_runs(white_cells, black, size)
            if any(len(run["cells"]) > 9 for run in runs):
                continue

            return {
                "size": size,
                "black_cells": sorted([r, c] for r, c in black),
                "runs": runs,
            }

        return None  # exhausted retries

    @staticmethod
    def _is_connected(white_cells: list, black: set, size: int) -> bool:
        """BFS connectivity check for the white interior cells."""
        white_set = set(white_cells)
        start = white_cells[0]
        visited = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in white_set and nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        return len(visited) == len(white_cells)


class KakuroFillGenerator:
    """Fill a Kakuro template with valid digit assignments (no-repeat per run).

    Only run-membership (no-repeat) is enforced during backtracking.  Run
    sums are derived from the final filled grid — they become the puzzle
    clues.

    Parameters
    ----------
    template:  Dict returned by :class:`KakuroTemplateLibrary`.
    seed:      RNG seed.
    """

    def __init__(self, template: dict, seed: int) -> None:
        self._template = template
        self._seed = seed
        self._rng = random.Random(seed)

    def fill(self, cancel_flag: list | None = None) -> list[list] | None:
        """Return a filled grid (list-of-lists) or *None* on failure."""
        template = self._template
        size = template["size"]
        runs = template["runs"]

        black_set = {(int(r), int(c)) for r, c in template["black_cells"]}
        white_cells = [
            (r, c) for r in range(size) for c in range(size)
            if (r, c) not in black_set
        ]

        # Run-based peer_cache: peers = all other cells in the same run(s).
        # This enforces no-repeat within each run via standard backtracking.
        peers: dict[tuple[int, int], set[tuple[int, int]]] = {
            wc: set() for wc in white_cells
        }
        for run in runs:
            cells = [(int(p[0]), int(p[1])) for p in run["cells"]]
            for cell in cells:
                peers[cell].update(c for c in cells if c != cell)
        peer_cache = {cell: frozenset(p) for cell, p in peers.items()}

        # Order cells by tightest run first (smallest run = most constrained).
        min_run_len: dict[tuple[int, int], int] = {}
        for run in runs:
            cells = [(int(p[0]), int(p[1])) for p in run["cells"]]
            rlen = len(cells)
            for cell in cells:
                if cell not in min_run_len or rlen < min_run_len[cell]:
                    min_run_len[cell] = rlen
        cell_order = sorted(white_cells, key=lambda c: min_run_len.get(c, size * size))

        grid: list[list] = [[None] * size for _ in range(size)]

        # Import here to avoid circular imports at module load time.
        from richards_sudoku.solver.generator import _fill_grid  # noqa: PLC0415

        # Kakuro always uses digits 1-9 (standard rule).
        symbols = list(range(1, 10))

        ok = _fill_grid(
            grid, list(cell_order), symbols, peer_cache, self._rng,
            cancel_flag=cancel_flag, cell_order=cell_order,
        )
        return grid if ok else None

