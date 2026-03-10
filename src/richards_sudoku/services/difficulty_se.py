"""SukakuExplainer-inspired difficulty rating for Sudoku variants.

Simulates human-style solving techniques in ascending difficulty order.
The puzzle's SE score is the weighted average of all technique applications
(sum of step weights divided by step count).  The score is mapped to a
human-readable category label.

Scoring
-------
score = sum(weight_i for each solving step i) / total_steps
score is capped at ``_BEYOND_WEIGHT`` (8.0).

If the grader cannot make forward progress (no available technique fires)
and finds a cell with an empty candidate set, the puzzle is considered
contradictory and ``(8.0, "Invalid")`` is returned.  An unsolvable-but-
non-contradictory puzzle (requiring techniques beyond this set) instead
returns ``(8.0, "Extreme")``.

Category thresholds
-------------------
<= 2.0  ->  Easy
<= 4.0  ->  Medium
<= 6.0  ->  Hard
 > 6.0  ->  Extreme  (or score equals _BEYOND_WEIGHT)

Variant support
---------------
Standard / Jigsaw
    Region-agnostic unit set; works out of the box.
Str8ts
    Additional run-sequence elimination applied when
    ``meta.constraints["black_cells"]`` is a list of ``[row, col]`` pairs
    marking black (blocked) cells.
Killer
    Additional cage-sum elimination applied when
    ``meta.constraints["cages"]`` is a list of
    ``{"cells": [[r, c], ...], "sum": N}`` dicts.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations, permutations
from typing import Sequence

from richards_sudoku.model.types import Board, VariantMetadata

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BEYOND_WEIGHT: float = 8.0
_INVALID_LABEL: str = "Invalid"


# ---------------------------------------------------------------------------
# Score → label
# ---------------------------------------------------------------------------

def score_to_label(score: float) -> str:
    """Return the difficulty category for a numeric SE score."""
    # TODO: calibrate per-variant thresholds after EV-T6 corpus
    if score <= 0.0:
        return "Unknown"
    if score <= 2.0:
        return "Easy"
    if score <= 4.0:
        return "Medium"
    if score <= 6.0:
        return "Hard"
    return "Extreme"


# ---------------------------------------------------------------------------
# Unit / peer construction
# ---------------------------------------------------------------------------

def _build_unit_groups(
    size: int,
    region_layout: Sequence[Sequence[int]],
    has_box_regions: bool = True,
) -> tuple[
    list[list[tuple[int, int]]],
    list[list[tuple[int, int]]],
    list[list[tuple[int, int]]],
]:
    """Return (row_units, col_units, region_units) for a size\u00d7size grid."""
    rows = [[(r, c) for c in range(size)] for r in range(size)]
    cols = [[(r, c) for r in range(size)] for c in range(size)]
    if not has_box_regions:
        # KenKen / Latin-square: no box-region uniqueness constraint.
        return rows, cols, []
    num_regions = (
        max(region_layout[r][c] for r in range(size) for c in range(size)) + 1
    )
    region_map: list[list[tuple[int, int]]] = [[] for _ in range(num_regions)]
    for r in range(size):
        for c in range(size):
            region_map[region_layout[r][c]].append((r, c))
    regions = [reg for reg in region_map if reg]
    return rows, cols, regions


def _build_peer_map(
    size: int,
    all_units: list[list[tuple[int, int]]],
) -> dict[tuple[int, int], frozenset[tuple[int, int]]]:
    """Build cell → frozenset-of-peers mapping."""
    raw: dict[tuple[int, int], set[tuple[int, int]]] = {
        (r, c): set() for r in range(size) for c in range(size)
    }
    for unit in all_units:
        for cell in unit:
            for peer in unit:
                if peer != cell:
                    raw[cell].add(peer)
    return {cell: frozenset(ps) for cell, ps in raw.items()}


# ---------------------------------------------------------------------------
# Working grid
# ---------------------------------------------------------------------------

class _WorkingGrid:
    """Mutable working copy of a puzzle used during SE simulation."""

    __slots__ = (
        "size", "symbols", "values", "candidates",
        "row_units", "col_units", "region_units", "units", "peers",
        "cell_to_region", "variant_name", "constraints", "black_cells",
    )

    def __init__(self, board: Board, meta: VariantMetadata) -> None:
        self.size: int = meta.size
        self.symbols: frozenset[int] = frozenset(meta.symbols)
        self.values: list[list[int | None]] = [
            [None] * meta.size for _ in range(meta.size)
        ]
        self.candidates: list[list[set[int]]] = [
            [set(meta.symbols) for _ in range(meta.size)]
            for _ in range(meta.size)
        ]

        rows, cols, regions = _build_unit_groups(
            meta.size,
            meta.region_layout,
            has_box_regions=meta.constraints.get("has_box_regions", True),
        )
        self.row_units = rows
        self.col_units = cols
        self.region_units = regions
        self.units = rows + cols + regions
        self.peers = _build_peer_map(meta.size, self.units)

        # Map each cell to its region list object (same object for all in region).
        self.cell_to_region: dict[tuple[int, int], list[tuple[int, int]]] = {}
        for reg in regions:
            for cell in reg:
                self.cell_to_region[cell] = reg

        self.variant_name: str = meta.name.value
        self.constraints: dict = meta.constraints  # type: ignore[type-arg]

        # SE-V1: Str8ts black cells — zero their candidates immediately
        self.black_cells: frozenset[tuple[int, int]] = frozenset(
            (int(p[0]), int(p[1]))
            for p in (self.constraints or {}).get("black_cells", [])
        )
        for r, c in self.black_cells:
            self.candidates[r][c] = set()

        # Seed from fixed clues only; player-entered values are ignored.
        for r in range(meta.size):
            for c in range(meta.size):
                cell = board.cell(r, c)
                if cell.is_fixed and cell.value is not None:
                    self.set_value(r, c, cell.value)

        # SE-V2: Killer-specific seeding
        if self.variant_name == "killer" and (self.constraints or {}).get("cages"):
            # (1) seed single-cell cages directly
            for cage in self.constraints["cages"]:
                cells = [(int(p[0]), int(p[1])) for p in cage.get("cells", [])]
                if len(cells) == 1:
                    r, c = cells[0]
                    if self.values[r][c] is None:
                        val = int(cage["sum"])
                        if val in self.candidates[r][c]:
                            self.set_value(r, c, val)
            # (2) one pass of cage elimination + propagate naked singles
            _killer_cage_step(self)
            for r in range(self.size):
                for c in range(self.size):
                    if self.values[r][c] is None and len(self.candidates[r][c]) == 1:
                        self.set_value(r, c, next(iter(self.candidates[r][c])))

        # SE-V3: KenKen-specific seeding — single-cell cages give value directly
        if self.variant_name == "kenken" and (self.constraints or {}).get("cages"):
            for cage in self.constraints["cages"]:
                cells = [(int(p[0]), int(p[1])) for p in cage.get("cells", [])]
                if len(cells) == 1:
                    r, c = cells[0]
                    target = int(cage.get("target", 0))
                    if self.values[r][c] is None and target in self.candidates[r][c]:
                        self.set_value(r, c, target)
            _kenken_cage_step(self)
            for r in range(self.size):
                for c in range(self.size):
                    if self.values[r][c] is None and len(self.candidates[r][c]) == 1:
                        self.set_value(r, c, next(iter(self.candidates[r][c])))

        # L5: Codewords-specific seeding from given_mappings
        if self.variant_name == "codewords":
            given_mappings: dict[str, int] = (self.constraints or {}).get("given_mappings", {})
            codebook: dict[str, int] = (self.constraints or {}).get("codebook", {})
            if given_mappings and codebook:
                # Build inverse codebook: digit → letter
                inv_codebook = {v: k for k, v in codebook.items()}
                # For each given (letter, digit) pair: set all board cells with that digit
                given_digits: set[int] = set(given_mappings.values())
                for r in range(meta.size):
                    for c in range(meta.size):
                        cell = board.cell(r, c)
                        if cell.value is not None and cell.value in given_digits:
                            if self.values[r][c] is None:
                                if cell.value in self.candidates[r][c]:
                                    self.set_value(r, c, cell.value)

        # SE-V4: Kakuro — override units to be run-based, then narrow candidates
        if self.variant_name == "kakuro" and (self.constraints or {}).get("clues"):
            run_units = [
                [(int(p[0]), int(p[1])) for p in run["cells"]]
                for run in self.constraints["clues"]
            ]
            self.row_units = []
            self.col_units = []
            self.region_units = run_units
            self.units = run_units
            self.peers = _build_peer_map(meta.size, run_units)
            # Seed: narrow candidates from run-sum + no-repeat until stable
            while _kakuro_run_step(self):
                pass
            for r in range(self.size):
                for c in range(self.size):
                    if self.values[r][c] is None and len(self.candidates[r][c]) == 1:
                        self.set_value(r, c, next(iter(self.candidates[r][c])))

    def is_solved(self) -> bool:
        return all(
            self.values[r][c] is not None
            for r in range(self.size)
            for c in range(self.size)
            if (r, c) not in self.black_cells
        )

    def set_value(self, r: int, c: int, val: int) -> None:
        self.values[r][c] = val
        self.candidates[r][c] = set()
        for pr, pc in self.peers[(r, c)]:
            self.candidates[pr][pc].discard(val)


# ---------------------------------------------------------------------------
# Shared elimination helpers
# ---------------------------------------------------------------------------

def _eliminate_from_unit(
    unit: list[tuple[int, int]],
    grid: _WorkingGrid,
    skip: set[tuple[int, int]],
    values: frozenset[int],
) -> bool:
    """Remove *values* from unsolved non-skip cells in *unit*."""
    changed = False
    for r, c in unit:
        if (r, c) not in skip and grid.values[r][c] is None:
            before = len(grid.candidates[r][c])
            grid.candidates[r][c] -= values
            if len(grid.candidates[r][c]) < before:
                changed = True
    return changed


def _reduce_cells_to(
    cells: frozenset[tuple[int, int]],
    values: set[int],
    grid: _WorkingGrid,
) -> bool:
    """Reduce each cell in *cells* to only *values*; return True if narrowed."""
    changed = False
    for r, c in cells:
        extra = grid.candidates[r][c] - values
        if extra:
            grid.candidates[r][c] -= extra
            changed = True
    return changed


def _elim_val_in_row_excl(
    grid: _WorkingGrid,
    val: int,
    row: int,
    excl: frozenset[tuple[int, int]],
) -> bool:
    """Discard *val* from *row* excluding *excl* cells."""
    changed = False
    for c in range(grid.size):
        cell = (row, c)
        if cell not in excl and grid.values[row][c] is None:
            if val in grid.candidates[row][c]:
                grid.candidates[row][c].discard(val)
                changed = True
    return changed


def _elim_val_in_col_excl(
    grid: _WorkingGrid,
    val: int,
    col: int,
    excl: frozenset[tuple[int, int]],
) -> bool:
    """Discard *val* from *col* excluding *excl* cells."""
    changed = False
    for r in range(grid.size):
        cell = (r, col)
        if cell not in excl and grid.values[r][col] is None:
            if val in grid.candidates[r][col]:
                grid.candidates[r][col].discard(val)
                changed = True
    return changed


def _elim_val_in_unit_excl(
    grid: _WorkingGrid,
    val: int,
    unit: list[tuple[int, int]],
    excl: frozenset[tuple[int, int]],
) -> bool:
    """Discard *val* from *unit* excluding *excl* cells."""
    changed = False
    for r, c in unit:
        if (r, c) not in excl and grid.values[r][c] is None:
            if val in grid.candidates[r][c]:
                grid.candidates[r][c].discard(val)
                changed = True
    return changed


# ---------------------------------------------------------------------------
# Step functions: Last Value, Hidden Single, Naked Single
# ---------------------------------------------------------------------------

def _last_value_in_unit(
    unit: list[tuple[int, int]],
    grid: _WorkingGrid,
) -> bool:
    """Place a value when only one empty cell remains in *unit*."""
    empty = [(r, c) for r, c in unit if grid.values[r][c] is None]
    if len(empty) != 1:
        return False
    r, c = empty[0]
    placed = {grid.values[pr][pc] for pr, pc in unit if grid.values[pr][pc] is not None}
    remaining = grid.symbols - placed
    if len(remaining) == 1:
        grid.set_value(r, c, next(iter(remaining)))
        return True
    return False


def _last_value_step(grid: _WorkingGrid) -> bool:
    for unit in grid.units:
        if _last_value_in_unit(unit, grid):
            return True
    return False


def _hidden_single_in_unit(
    unit: list[tuple[int, int]],
    grid: _WorkingGrid,
) -> bool:
    counts: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, c in unit:
        if grid.values[r][c] is None:
            for val in grid.candidates[r][c]:
                counts[val].append((r, c))
    for val, cells in counts.items():
        if len(cells) == 1:
            grid.set_value(cells[0][0], cells[0][1], val)
            return True
    return False


def _hidden_single_step(
    units: list[list[tuple[int, int]]],
    grid: _WorkingGrid,
) -> bool:
    for unit in units:
        if _hidden_single_in_unit(unit, grid):
            return True
    return False


def _naked_single_step(grid: _WorkingGrid) -> bool:
    for r in range(grid.size):
        for c in range(grid.size):
            cands = grid.candidates[r][c]
            if grid.values[r][c] is None and len(cands) == 1:
                grid.set_value(r, c, next(iter(cands)))
                return True
    return False


# ---------------------------------------------------------------------------
# Pointing (locked candidates: region → row/col)
# ---------------------------------------------------------------------------

def _pointing_in_region(
    reg: list[tuple[int, int]],
    grid: _WorkingGrid,
) -> bool:
    reg_set = frozenset(reg)
    for val in grid.symbols:
        with_val = [
            (r, c) for r, c in reg
            if grid.values[r][c] is None and val in grid.candidates[r][c]
        ]
        if len(with_val) < 2:
            continue
        rows = {r for r, _c in with_val}
        cols = {c for _r, c in with_val}
        if len(rows) == 1:
            if _elim_val_in_row_excl(grid, val, next(iter(rows)), reg_set):
                return True
        if len(cols) == 1:
            if _elim_val_in_col_excl(grid, val, next(iter(cols)), reg_set):
                return True
    return False


def _pointing_step(grid: _WorkingGrid) -> bool:
    for reg in grid.region_units:
        if _pointing_in_region(reg, grid):
            return True
    return False


# ---------------------------------------------------------------------------
# Claiming (locked candidates: row/col → region)
# ---------------------------------------------------------------------------

def _claiming_in_line(
    line: list[tuple[int, int]],
    grid: _WorkingGrid,
) -> bool:
    line_set = frozenset(line)
    for val in grid.symbols:
        with_val = [
            (r, c) for r, c in line
            if grid.values[r][c] is None and val in grid.candidates[r][c]
        ]
        if len(with_val) < 2:
            continue
        reg0 = grid.cell_to_region.get(with_val[0])
        if reg0 is None:
            continue
        all_same = all(
            grid.cell_to_region.get((r, c)) is reg0
            for r, c in with_val[1:]
        )
        if all_same and _elim_val_in_unit_excl(grid, val, reg0, line_set):
            return True
    return False


def _claiming_step(grid: _WorkingGrid) -> bool:
    for line in grid.row_units + grid.col_units:
        if _claiming_in_line(line, grid):
            return True
    return False


# ---------------------------------------------------------------------------
# Naked / Hidden subsets (pair=2, triple=3, quad=4)
# ---------------------------------------------------------------------------

def _naked_subset_in_unit(
    n: int,
    unit: list[tuple[int, int]],
    grid: _WorkingGrid,
) -> bool:
    empties = [
        (r, c) for r, c in unit
        if grid.values[r][c] is None and 1 < len(grid.candidates[r][c]) <= n
    ]
    for combo in combinations(empties, n):
        combined: set[int] = set()
        for r, c in combo:
            combined |= grid.candidates[r][c]
        if len(combined) != n:
            continue
        if _eliminate_from_unit(unit, grid, set(combo), frozenset(combined)):
            return True
    return False


def _hidden_subset_in_unit(
    n: int,
    unit: list[tuple[int, int]],
    grid: _WorkingGrid,
) -> bool:
    counts: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, c in unit:
        if grid.values[r][c] is None:
            for val in grid.candidates[r][c]:
                counts[val].append((r, c))
    twos_to_n = {
        val: frozenset(cells)
        for val, cells in counts.items()
        if 2 <= len(cells) <= n
    }
    vals = list(twos_to_n)
    for combo in combinations(vals, n):
        cell_union = frozenset().union(*(twos_to_n[v] for v in combo))
        if len(cell_union) != n:
            continue
        if _reduce_cells_to(cell_union, set(combo), grid):
            return True
    return False


# ---------------------------------------------------------------------------
# Generalised fish (X-Wing=2, Swordfish=3, Jellyfish=4)
# ---------------------------------------------------------------------------

def _elim_val_in_cols_skip(
    grid: _WorkingGrid,
    val: int,
    skip_rows: frozenset[int],
    target_cols: frozenset[int],
) -> bool:
    changed = False
    for r in range(grid.size):
        if r in skip_rows:
            continue
        for c in target_cols:
            if grid.values[r][c] is None and val in grid.candidates[r][c]:
                grid.candidates[r][c].discard(val)
                changed = True
    return changed


def _elim_val_in_rows_skip(
    grid: _WorkingGrid,
    val: int,
    skip_cols: frozenset[int],
    target_rows: frozenset[int],
) -> bool:
    changed = False
    for c in range(grid.size):
        if c in skip_cols:
            continue
        for r in target_rows:
            if grid.values[r][c] is None and val in grid.candidates[r][c]:
                grid.candidates[r][c].discard(val)
                changed = True
    return changed


def _fish_row_based(degree: int, val: int, grid: _WorkingGrid) -> bool:
    row_cols: dict[int, list[int]] = {}
    for r in range(grid.size):
        cols = [
            c for c in range(grid.size)
            if grid.values[r][c] is None and val in grid.candidates[r][c]
        ]
        if 2 <= len(cols) <= degree:
            row_cols[r] = cols
    for rows in combinations(row_cols, degree):
        all_cols = frozenset().union(*(row_cols[r] for r in rows))
        if len(all_cols) == degree:
            if _elim_val_in_cols_skip(grid, val, frozenset(rows), all_cols):
                return True
    return False


def _fish_col_based(degree: int, val: int, grid: _WorkingGrid) -> bool:
    col_rows: dict[int, list[int]] = {}
    for c in range(grid.size):
        rows = [
            r for r in range(grid.size)
            if grid.values[r][c] is None and val in grid.candidates[r][c]
        ]
        if 2 <= len(rows) <= degree:
            col_rows[c] = rows
    for cols in combinations(col_rows, degree):
        all_rows = frozenset().union(*(col_rows[c] for c in cols))
        if len(all_rows) == degree:
            if _elim_val_in_rows_skip(grid, val, frozenset(cols), all_rows):
                return True
    return False


def _fish_step(degree: int, val: int, grid: _WorkingGrid) -> bool:
    return _fish_row_based(degree, val, grid) or _fish_col_based(degree, val, grid)


# ---------------------------------------------------------------------------
# Str8ts run elimination
# ---------------------------------------------------------------------------

def _get_str8ts_runs(
    line_cells: list[tuple[int, int]],
    black_set: set[tuple[int, int]],
) -> list[list[tuple[int, int]]]:
    """Return runs (white-cell sequences) in *line_cells* split by blacks."""
    runs: list[list[tuple[int, int]]] = []
    current: list[tuple[int, int]] = []
    for cell in line_cells:
        if cell in black_set:
            if len(current) > 1:
                runs.append(current)
            current = []
        else:
            current.append(cell)
    if len(current) > 1:
        runs.append(current)
    return runs


def _str8ts_run_eliminations(
    run_cells: list[tuple[int, int]],
    grid: _WorkingGrid,
) -> bool:
    """Remove candidates that cannot be part of a consecutive run of the
    right length in *run_cells*.
    """
    n = len(run_cells)
    # Collect all currently possible digits across the run.
    all_cands: set[int] = set()
    for r, c in run_cells:
        if grid.values[r][c] is None:
            all_cands |= grid.candidates[r][c]
        elif grid.values[r][c] is not None:
            all_cands.add(grid.values[r][c])  # type: ignore[arg-type]
    # A window of length n where every digit is represented somewhere.
    valid_starts = [
        k for k in range(1, grid.size - n + 2)
        if all(d in all_cands for d in range(k, k + n))
    ]
    if not valid_starts:
        return False  # no valid window; puzzle may be invalid but skip here
    valid_digits = {d for k in valid_starts for d in range(k, k + n)}
    changed = False
    for r, c in run_cells:
        if grid.values[r][c] is None:
            before = len(grid.candidates[r][c])
            grid.candidates[r][c] &= valid_digits
            if len(grid.candidates[r][c]) < before:
                changed = True
    return changed


def _str8ts_step(grid: _WorkingGrid) -> bool:
    black_raw = grid.constraints.get("black_cells", [])
    black_set: set[tuple[int, int]] = {(int(p[0]), int(p[1])) for p in black_raw}
    for line in grid.row_units + grid.col_units:
        for run in _get_str8ts_runs(line, black_set):
            if _str8ts_run_eliminations(run, grid):
                return True
    return False


# ---------------------------------------------------------------------------
# Killer cage elimination
# ---------------------------------------------------------------------------

def _perm_fits_cells(
    perm: tuple[int, ...],
    cells: list[tuple[int, int]],
    grid: _WorkingGrid,
) -> bool:
    for i, (r, c) in enumerate(cells):
        if grid.values[r][c] is not None:
            if grid.values[r][c] != perm[i]:
                return False
        elif perm[i] not in grid.candidates[r][c]:
            return False
    return True


_CAGE_PERM_CAP = 10_000


def _cage_valid_values(
    cells: list[tuple[int, int]],
    cage_sum: int,
    grid: _WorkingGrid,
) -> list[set[int]]:
    """Return per-cell set of values that appear in any valid cage assignment.

    SE-V3: Caps total permutations tested at _CAGE_PERM_CAP to keep grading
    fast for large cages (≥5 cells).  Cages with fewer than 5 cells enumerate
    all permutations without a cap.  When the cap is hit the function returns
    whatever candidates have been narrowed so far — it never over-eliminates.
    """
    n = len(cells)
    valid_per_cell: list[set[int]] = [set() for _ in range(n)]
    count = 0
    apply_cap = n >= 5
    for combo in combinations(grid.symbols, n):
        if sum(combo) != cage_sum:
            continue
        for perm in permutations(combo):
            if _perm_fits_cells(perm, cells, grid):
                for i, val in enumerate(perm):
                    valid_per_cell[i].add(val)
            if apply_cap:
                count += 1
                if count >= _CAGE_PERM_CAP:
                    return valid_per_cell
    return valid_per_cell


def _eliminate_from_cage(
    cells: list[tuple[int, int]],
    valid_per_cell: list[set[int]],
    grid: _WorkingGrid,
) -> bool:
    changed = False
    for i, (r, c) in enumerate(cells):
        if grid.values[r][c] is not None:
            continue
        if not valid_per_cell[i]:
            continue
        before = len(grid.candidates[r][c])
        grid.candidates[r][c] &= valid_per_cell[i]
        if len(grid.candidates[r][c]) < before:
            changed = True
    return changed


def _apply_cage_elimination(
    cells: list[tuple[int, int]],
    cage_sum: int,
    grid: _WorkingGrid,
) -> bool:
    valid_per_cell = _cage_valid_values(cells, cage_sum, grid)
    return _eliminate_from_cage(cells, valid_per_cell, grid)


def _killer_cage_step(grid: _WorkingGrid) -> bool:
    for cage in grid.constraints.get("cages", []):
        cells = [(int(p[0]), int(p[1])) for p in cage.get("cells", [])]
        cage_sum = int(cage.get("sum", 0))
        if not cells or cage_sum <= 0:
            continue
        if _apply_cage_elimination(cells, cage_sum, grid):
            return True
    return False


def _kenken_cage_valid_values(
    cells: list[tuple[int, int]],
    op: str,
    target: int,
    grid: _WorkingGrid,
) -> list[set[int]]:
    """Return per-cell valid value sets satisfying one KenKen cage constraint."""
    n = len(cells)
    valid_per_cell: list[set[int]] = [set() for _ in range(n)]
    if n == 1:
        r, c = cells[0]
        if target in grid.candidates[r][c]:
            valid_per_cell[0].add(target)
        return valid_per_cell
    if op == "+":
        apply_cap = n >= 5
        count = 0
        for combo in combinations(grid.symbols, n):
            if sum(combo) != target:
                continue
            for perm in permutations(combo):
                if _perm_fits_cells(perm, cells, grid):
                    for i, val in enumerate(perm):
                        valid_per_cell[i].add(val)
                if apply_cap:
                    count += 1
                    if count >= _CAGE_PERM_CAP:
                        return valid_per_cell
    elif op == "*":
        apply_cap = n >= 5
        count = 0
        for combo in combinations(grid.symbols, n):
            prod = 1
            for v in combo:
                prod *= v
            if prod != target:
                continue
            for perm in permutations(combo):
                if _perm_fits_cells(perm, cells, grid):
                    for i, val in enumerate(perm):
                        valid_per_cell[i].add(val)
                if apply_cap:
                    count += 1
                    if count >= _CAGE_PERM_CAP:
                        return valid_per_cell
    elif op == "-" and n == 2:
        for a, b in combinations(grid.symbols, 2):
            if abs(a - b) != target:
                continue
            if _perm_fits_cells((a, b), cells, grid):
                valid_per_cell[0].add(a)
                valid_per_cell[1].add(b)
            if _perm_fits_cells((b, a), cells, grid):
                valid_per_cell[0].add(b)
                valid_per_cell[1].add(a)
    elif op == "/" and n == 2:
        for a, b in combinations(grid.symbols, 2):
            big, small = max(a, b), min(a, b)
            if small == 0 or big % small != 0 or big // small != target:
                continue
            if _perm_fits_cells((a, b), cells, grid):
                valid_per_cell[0].add(a)
                valid_per_cell[1].add(b)
            if _perm_fits_cells((b, a), cells, grid):
                valid_per_cell[0].add(b)
                valid_per_cell[1].add(a)
    return valid_per_cell


def _kenken_cage_step(grid: _WorkingGrid) -> bool:
    """One pass of KenKen cage arithmetic elimination."""
    for cage in grid.constraints.get("cages", []):
        cells = [(int(p[0]), int(p[1])) for p in cage.get("cells", [])]
        op = cage.get("op", "+")
        target = int(cage.get("target", 0))
        if not cells or target <= 0:
            continue
        valid_per_cell = _kenken_cage_valid_values(cells, op, target, grid)
        if _eliminate_from_cage(cells, valid_per_cell, grid):
            return True
    return False


# ---------------------------------------------------------------------------
# Validity helpers
# ---------------------------------------------------------------------------

def _has_empty_candidates(grid: _WorkingGrid) -> bool:
    """Return True if any unsolved non-black cell has no remaining candidates."""
    for r in range(grid.size):
        for c in range(grid.size):
            if (r, c) not in grid.black_cells and grid.values[r][c] is None and len(grid.candidates[r][c]) == 0:
                return True
    return False


def _is_seeding_valid(grid: _WorkingGrid) -> bool:
    """Return False if any unit contains duplicate solved values (contradiction)."""
    for unit in grid.units:
        placed = [grid.values[r][c] for r, c in unit if grid.values[r][c] is not None]
        if len(placed) != len(set(placed)):
            return False
    return True


# ---------------------------------------------------------------------------
# Technique classes (thin wrappers)
# ---------------------------------------------------------------------------

class _LastValue:
    name = "Last Value"
    weight = 1.0

    def apply(self, grid: _WorkingGrid) -> bool:
        return _last_value_step(grid)


class _CodewordsMapping:
    """Codewords letter-to-digit mapping technique (weight 1.3).

    Fires when every cell bearing an unassigned letter L is a digit-singleton
    AND all those singletons agree on the same digit d.  The technique then
    sets d for all such cells simultaneously.

    Condition (spec L5, Option B): ALL cells bearing letter L must be reduced
    to a single candidate before the technique fires; if any cell bearing L
    has multiple candidates, the technique blocks for letter L.
    """

    name = "Codewords Mapping"
    weight = 1.3

    def apply(self, grid: _WorkingGrid) -> bool:
        if grid.variant_name != "codewords":
            return False
        codebook: dict[str, int] = (grid.constraints or {}).get("codebook", {})
        if not codebook:
            return False

        # Build inverse codebook: digit → letter
        inv_codebook = {v: k for k, v in codebook.items()}
        size = grid.size
        progress = False

        # Group unsolved cells by their letter (i.e. by the digit they would display)
        # A cell at (r,c) with no value yet groups under letter = inv_codebook[cand_digit]
        # But cells may have multiple candidates — we need to group by "which letter
        # would this cell represent in the final solution?"
        # In Codewords, each cell position maps to a unique letter in the solution.
        # However before solving we don't know which digit/letter a cell will take.
        # The technique: for each letter L (digit d = codebook[L]):
        #   - collect all cells whose candidates are a subset of {d} (i.e. singleton {d})
        #     OR whose candidates include d (candidate d is still possible)
        # Per spec (Option B): ALL cells in the puzzle that will become letter L
        # must be singleton before firing. But we don't know which cells will be L
        # without solving. Practical interpretation: for each digit d, collect cells
        # whose ONLY candidate is {d}. If all puzzle cells that could carry d form
        # a unanimous singleton set, set them.
        #
        # Refined interpretation matching spec: iterate all unsolved cells;
        # for each unassigned digit d, check if every cell that has d as its ONLY
        # candidate forms a "letter d block". If so, set them all (no new info
        # beyond naked single, but fires as a named technique).
        # More useful: the cross-cell constraint — if cell A has only {d} and
        # cell B also has only {d} but they're not peers, they'd conflict.
        # The real power: propagate via codebook bijection — once one letter is
        # pinned, all instances get set.
        #
        # Simplest faithful implementation matching spec Option B:
        # For each letter L (=digit d):
        #   cells_L = all unsolved cells that have d among their candidates
        #   if ALL cells_L are singletons {d}: set them all → progress

        # Build: digit → list of unsolved cells that have that digit as candidate
        from collections import defaultdict
        digit_cells: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for r in range(size):
            for c in range(size):
                if grid.values[r][c] is None:
                    for d in grid.candidates[r][c]:
                        digit_cells[d].append((r, c))

        for d, cells in digit_cells.items():
            # All cells that still have d must be singletons {d}
            if all(grid.candidates[r][c] == {d} for r, c in cells):
                for r, c in cells:
                    grid.set_value(r, c, d)
                    progress = True

        return progress


class _HiddenSingleBlock:
    name = "Hidden Single (Block)"
    weight = 1.2

    def apply(self, grid: _WorkingGrid) -> bool:
        return _hidden_single_step(grid.region_units, grid)


class _HiddenSingleLinear:
    name = "Hidden Single (Row/Col)"
    weight = 1.5

    def apply(self, grid: _WorkingGrid) -> bool:
        return _hidden_single_step(grid.row_units + grid.col_units, grid)


class _Str8tsRun:
    name = "Str8ts Run"
    weight = 1.7

    def apply(self, grid: _WorkingGrid) -> bool:
        if grid.variant_name != "str8ts":
            return False
        return _str8ts_step(grid)


class _KillerCage:
    name = "Killer Cage"
    weight = 1.9

    def apply(self, grid: _WorkingGrid) -> bool:
        if not grid.constraints.get("cages"):
            return False
        return _killer_cage_step(grid)


class _KenKenCage:
    name = "KenKen Cage"
    weight = 1.9

    def apply(self, grid: _WorkingGrid) -> bool:
        if grid.variant_name != "kenken":
            return False
        if not grid.constraints.get("cages"):
            return False
        return _kenken_cage_step(grid)


def _kakuro_can_reach(needed: int, count: int, used: set) -> bool:
    """Return True if *count* distinct digits from 1-9 (not in *used*) can sum to *needed*."""
    if count == 0:
        return needed == 0
    avail = [v for v in range(1, 10) if v not in used]
    if len(avail) < count:
        return False
    avail_s = sorted(avail)
    return avail_s[0] <= needed // count and sum(avail_s[:count]) <= needed <= sum(avail_s[-count:])


def _kakuro_run_step(grid: _WorkingGrid) -> bool:
    """One pass of Kakuro run-sum and no-repeat candidate elimination."""
    changed = False
    for run in grid.constraints.get("clues", []):
        cells = [(int(p[0]), int(p[1])) for p in run["cells"]]
        target = int(run["sum"])
        filled_vals = {grid.values[r][c] for r, c in cells if grid.values[r][c] is not None}
        filled_sum = sum(grid.values[r][c] for r, c in cells if grid.values[r][c] is not None)
        unfilled = [(r, c) for r, c in cells if grid.values[r][c] is None]
        if not unfilled:
            continue
        needed = target - filled_sum
        n_remaining = len(unfilled)
        for r, c in unfilled:
            to_remove: set[int] = set()
            for v in list(grid.candidates[r][c]):
                if v in filled_vals:
                    to_remove.add(v)
                    continue
                used = filled_vals | {v}
                if not _kakuro_can_reach(needed - v, n_remaining - 1, used):
                    to_remove.add(v)
            if to_remove:
                grid.candidates[r][c] -= to_remove
                changed = True
    return changed


class _KakuroRun:
    name = "Kakuro Run"
    weight = 2.1

    def apply(self, grid: _WorkingGrid) -> bool:
        if grid.variant_name != "kakuro":
            return False
        if not grid.constraints.get("clues"):
            return False
        return _kakuro_run_step(grid)


class _NakedSingle:
    name = "Naked Single"
    weight = 2.3

    def apply(self, grid: _WorkingGrid) -> bool:
        return _naked_single_step(grid)


class _Pointing:
    name = "Pointing"
    weight = 2.6

    def apply(self, grid: _WorkingGrid) -> bool:
        return _pointing_step(grid)


class _Claiming:
    name = "Claiming"
    weight = 2.8

    def apply(self, grid: _WorkingGrid) -> bool:
        return _claiming_step(grid)


class _NakedPair:
    name = "Naked Pair"
    weight = 3.0

    def apply(self, grid: _WorkingGrid) -> bool:
        for unit in grid.units:
            if _naked_subset_in_unit(2, unit, grid):
                return True
        return False


class _XWing:
    name = "X-Wing"
    weight = 3.2

    def apply(self, grid: _WorkingGrid) -> bool:
        for val in grid.symbols:
            if _fish_step(2, val, grid):
                return True
        return False


class _HiddenPair:
    name = "Hidden Pair"
    weight = 3.4

    def apply(self, grid: _WorkingGrid) -> bool:
        for unit in grid.units:
            if _hidden_subset_in_unit(2, unit, grid):
                return True
        return False


class _NakedTriple:
    name = "Naked Triple"
    weight = 3.6

    def apply(self, grid: _WorkingGrid) -> bool:
        for unit in grid.units:
            if _naked_subset_in_unit(3, unit, grid):
                return True
        return False


class _Swordfish:
    name = "Swordfish"
    weight = 3.8

    def apply(self, grid: _WorkingGrid) -> bool:
        for val in grid.symbols:
            if _fish_step(3, val, grid):
                return True
        return False


class _HiddenTriple:
    name = "Hidden Triple"
    weight = 4.0

    def apply(self, grid: _WorkingGrid) -> bool:
        for unit in grid.units:
            if _hidden_subset_in_unit(3, unit, grid):
                return True
        return False


class _NakedQuad:
    name = "Naked Quad"
    weight = 5.0

    def apply(self, grid: _WorkingGrid) -> bool:
        for unit in grid.units:
            if _naked_subset_in_unit(4, unit, grid):
                return True
        return False


class _Jellyfish:
    name = "Jellyfish"
    weight = 5.2

    def apply(self, grid: _WorkingGrid) -> bool:
        for val in grid.symbols:
            if _fish_step(4, val, grid):
                return True
        return False


class _HiddenQuad:
    name = "Hidden Quad"
    weight = 5.4

    def apply(self, grid: _WorkingGrid) -> bool:
        for unit in grid.units:
            if _hidden_subset_in_unit(4, unit, grid):
                return True
        return False


# ---------------------------------------------------------------------------
# Technique registry (ascending weight)
# ---------------------------------------------------------------------------

_TECHNIQUES: list = [
    _LastValue(),
    _CodewordsMapping(),
    _HiddenSingleBlock(),
    _HiddenSingleLinear(),
    _Str8tsRun(),
    _KillerCage(),
    _KenKenCage(),
    _KakuroRun(),
    _NakedSingle(),
    _Pointing(),
    _Claiming(),
    _NakedPair(),
    _XWing(),
    _HiddenPair(),
    _NakedTriple(),
    _Swordfish(),
    _HiddenTriple(),
    _NakedQuad(),
    _Jellyfish(),
    _HiddenQuad(),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def grade(board: Board, meta: VariantMetadata) -> tuple[float, str]:
    """Grade puzzle difficulty using cumulative SE-style technique simulation.

    Only ``cell.is_fixed`` clues are used as the starting position;
    player-entered values are ignored so the rating reflects intrinsic
    puzzle difficulty.

    Parameters
    ----------
    board:
        Current board (fixed clues read; player values ignored).
    meta:
        Variant metadata supplying size, symbols, and region layout.

    Returns
    -------
    (score, label)
        score:
            Weighted average of technique weights across all solving steps,
            capped at ``_BEYOND_WEIGHT`` (8.0).
        label:
            ``"Invalid"`` when a contradiction is detected (unsolvable clues).
            ``"Unknown"`` when the board has no empty cells to grade.
            Otherwise one of: Easy / Medium / Hard / Extreme.
    """
    grid = _WorkingGrid(board, meta)

    if not _is_seeding_valid(grid):
        return (_BEYOND_WEIGHT, _INVALID_LABEL)

    total_weight = 0.0
    step_count = 0

    while not grid.is_solved():
        progress = False
        for tech in _TECHNIQUES:
            if tech.apply(grid):
                total_weight += tech.weight
                step_count += 1
                progress = True
                break
        if not progress:
            if _has_empty_candidates(grid):
                return (_BEYOND_WEIGHT, _INVALID_LABEL)
            # Valid but requires techniques beyond our set.
            return (_BEYOND_WEIGHT, score_to_label(_BEYOND_WEIGHT))

    if step_count == 0:
        return (0.0, "Unknown")

    score = min(total_weight / step_count, _BEYOND_WEIGHT)
    return score, score_to_label(score)
