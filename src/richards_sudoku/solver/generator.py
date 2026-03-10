"""Seedable puzzle generator for Sudoku variants.

Generates a fully-filled solution grid, then removes clues while
ensuring the remaining puzzle has a unique solution.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Callable, Sequence

from richards_sudoku.solver.solver import Grid, _build_peer_cache, _build_region_units, _candidates, validate
from richards_sudoku.model.types import VariantMetadata


# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------

class GenerationCancelled(Exception):
    """Raised when a background worker requests cooperative cancellation."""


# ---------------------------------------------------------------------------
# Full-grid generator
# ---------------------------------------------------------------------------

def _fill_grid(
    grid: Grid,
    remaining: list[tuple[int, int]],
    symbols: list[int],
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]],
    rng: random.Random,
    meta: object = None,
    constraint_ok: Callable[[Grid], bool] | None = None,
    cancel_flag: list[bool] | None = None,
    cell_order: list[tuple[int, int]] | None = None,
) -> bool:
    """Fill *grid* using randomised backtracking with MRV heuristic + forward checking.

    MRV (Minimum Remaining Values): at each step pick the unfilled cell with
    the fewest legal candidates.  This dramatically shrinks the search tree
    for irregular-region variants such as Jigsaw.  Forward checking returns
    False immediately when any unfilled cell has zero candidates.

    When *cell_order* is provided it defines the initial ordering of cells to
    fill (tightest-run-first for Kakuro).  MRV still applies from the second
    step onwards.
    """
    if cell_order is not None:
        # Rebuild remaining in the requested order, skipping already-filled cells.
        remaining = [c for c in cell_order if grid[c[0]][c[1]] is None]

    if cancel_flag is not None and cancel_flag[0]:
        return False

    if not remaining:
        if constraint_ok is not None and not constraint_ok(grid):
            return False
        return True

    # MRV: find the cell with the fewest candidates (fail fast on 0)
    best_idx = 0
    best_count = len(symbols) + 1
    for i, (r, c) in enumerate(remaining):
        n = len(_candidates(grid, r, c, symbols, peer_cache))
        if n == 0:
            return False  # forward check: dead end
        if n < best_count:
            best_count = n
            best_idx = i
            if best_count == 1:
                break  # can't do better

    row, col = remaining[best_idx]
    cands = list(_candidates(grid, row, col, symbols, peer_cache))
    rng.shuffle(cands)
    remaining.pop(best_idx)
    for val in cands:
        grid[row][col] = val
        if _fill_grid(grid, remaining, symbols, peer_cache, rng, meta, constraint_ok, cancel_flag):
            return True
        grid[row][col] = None
    remaining.insert(best_idx, (row, col))
    return False


def generate_solution(
    size: int,
    region_layout: Sequence[Sequence[int]],
    symbols: list[int],
    seed: int | None = None,
    meta: object = None,
    constraint_ok: Callable[[Grid], bool] | None = None,
    cancel_flag: list[bool] | None = None,
) -> Grid:
    """Return a randomly-filled, valid, complete grid.

    Args:
        size: board dimension.
        region_layout: size×size mapping (row,col) -> region_id.
        symbols: allowed fill values.
        seed: RNG seed for reproducibility; None for random.
        meta: optional variant metadata (passed through to _fill_grid).
        constraint_ok: optional extra constraint function called on the
            completed grid; if it returns False the fill is retried.
        cancel_flag: single-element list; set [True] to request cancellation.

    Raises:
        RuntimeError: if filling fails (should not happen for valid metadata).
        GenerationCancelled: if cancel_flag is set during filling.
    """
    rng = random.Random(seed)
    peer_cache = _build_peer_cache(size, region_layout)
    grid: Grid = [[None] * size for _ in range(size)]
    remaining = [(r, c) for r in range(size) for c in range(size)]
    if not _fill_grid(grid, remaining, symbols, peer_cache, rng, meta, constraint_ok, cancel_flag):
        if cancel_flag is not None and cancel_flag[0]:
            raise GenerationCancelled()
        raise RuntimeError("Failed to generate a solution grid – check variant metadata.")
    return grid


# ---------------------------------------------------------------------------
# Puzzle generator  (solution → unique puzzle by removing clues)
# ---------------------------------------------------------------------------

def _count_solutions(
    grid: Grid,
    remaining: list[tuple[int, int]],
    symbols: list[int],
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]],
    cancel_flag: list[bool] | None = None,
    constraint_ok: Callable[[Grid], bool] | None = None,
    region_units: list[list[tuple[int, int]]] | None = None,
) -> int:
    """Count solutions up to 2 using constraint propagation + MRV backtracking.

    Builds a mutable candidate map once and maintains it incrementally via a
    trail-based undo mechanism.  Propagates naked singles, row hidden singles,
    column hidden singles, and (when *region_units* is supplied) box/region
    hidden singles eagerly at every node.  For well-constrained grids such as
    standard 25×25 Sudoku this eliminates virtually all branching and reduces
    the per-call cost from O(N²·K) to O(N·K).
    """
    if cancel_flag is not None and cancel_flag[0]:
        return 0

    if not remaining:
        if constraint_ok is not None and not constraint_ok(grid):
            return 0
        return 1

    sym_set = set(symbols)
    size = max(r for r, _ in remaining) + 1 if remaining else 0

    # Build one mutable candidate set per empty cell.
    cand_map: dict[tuple[int, int], set[int]] = {}
    for r, c in remaining:
        used = {grid[pr][pc] for pr, pc in peer_cache[(r, c)] if grid[pr][pc] is not None}
        cands = sym_set - used
        if not cands:
            return 0  # immediate contradiction
        cand_map[(r, c)] = cands

    # Precompute cell→region-index map for region hidden singles.
    cell_region: dict[tuple[int, int], int] | None = None
    if region_units is not None:
        cell_region = {}
        for rid, unit in enumerate(region_units):
            for cell in unit:
                cell_region[cell] = rid

    # Trail entries encode undo operations:
    #   (0, (r,c), None)  → restore grid[r][c] = None
    #   (1, (r,c), saved) → restore cand_map[(r,c)] = saved
    #   (2, (r,c), val)   → restore val into cand_map[(r,c)]

    def _assign(cell: tuple[int, int], val: int, trail: list) -> bool:
        """Place *val* in *cell*, propagate to peers. Return False on contradiction."""
        r, c = cell
        grid[r][c] = val
        trail.append((0, cell, None))
        saved = cand_map.pop(cell)
        trail.append((1, cell, saved))
        for nb in peer_cache[cell]:
            if nb in cand_map:
                peer_cands = cand_map[nb]
                if val in peer_cands:
                    peer_cands.discard(val)
                    trail.append((2, nb, val))
                    if not peer_cands:
                        return False
        return True

    def _undo(trail: list) -> None:
        for kind, cell, data in reversed(trail):
            if kind == 0:
                grid[cell[0]][cell[1]] = None
            elif kind == 1:
                cand_map[cell] = data
            else:
                cand_map[cell].add(data)

    def _propagate(trail: list) -> bool:
        """Propagate until stable using naked singles, hidden singles
        (rows/cols/regions), locking type 1 & 2, and naked pairs.

        All look-up maps are built in ONE scan per outer-loop pass and reused
        for every technique.  Hidden-singles checks apply a staleness filter
        (len>1 entries may shrink to 1 after earlier assignments in the same
        pass), which eliminates most of the deep backtracking seen previously.
        """
        while True:
            changed_flag = False

            # ── 1. Naked singles ─────────────────────────────────────────────
            # Restart immediately – no map rebuild needed.
            for cell in list(cand_map):
                if cell not in cand_map:
                    continue
                cands = cand_map[cell]
                if len(cands) == 0:
                    return False
                if len(cands) == 1:
                    val = next(iter(cands))
                    if not _assign(cell, val, trail):
                        return False
                    changed_flag = True
            if changed_flag:
                continue

            # ── 2. Build all maps in ONE scan ────────────────────────────────
            # row_val[(r,v)] / col_val[(c,v)] / reg_val[(rid,v)] list the cells
            # that have v as a candidate.  Reused for hidden singles AND locking.
            # cells_by_row/col/reg are used for the naked-pairs step.
            row_val: dict[tuple[int, int], list] = defaultdict(list)
            col_val: dict[tuple[int, int], list] = defaultdict(list)
            reg_val: dict[tuple[int, int], list] | None = (
                defaultdict(list) if cell_region is not None else None
            )
            cells_by_row: dict[int, list] = defaultdict(list)
            cells_by_col: dict[int, list] = defaultdict(list)
            cells_by_reg: dict[int, list] | None = (
                defaultdict(list) if cell_region is not None else None
            )
            for cell, cands in cand_map.items():
                r, c = cell
                cells_by_row[r].append(cell)
                cells_by_col[c].append(cell)
                if cell_region is not None:
                    rid = cell_region[cell]
                    if cells_by_reg is not None:
                        cells_by_reg[rid].append(cell)
                for v in cands:
                    row_val[(r, v)].append(cell)
                    col_val[(c, v)].append(cell)
                    if reg_val is not None:
                        reg_val[(rid, v)].append(cell)

            # ── 3-5. Hidden singles ───────────────────────────────────────────
            # STALENESS FIX: earlier assignments within this outer-loop pass can
            # reduce a map entry from len>1 to an effective len of 1.  We apply
            # a fast filter for every entry, not just the originally-unit ones.
            for val_map in (
                row_val,
                col_val,
                *([] if reg_val is None else [reg_val]),
            ):
                for (_, v), cells in val_map.items():
                    if len(cells) == 1:
                        # Fast path: originally a singleton.
                        cell = cells[0]
                        if cell in cand_map and v in cand_map[cell]:
                            if not _assign(cell, v, trail):
                                return False
                            changed_flag = True
                    else:
                        # Staleness check: earlier assignments may have reduced
                        # the effective candidate list to exactly one cell.
                        valid = [
                            c for c in cells
                            if c in cand_map and v in cand_map[c]
                        ]
                        if len(valid) == 1:
                            if not _assign(valid[0], v, trail):
                                return False
                            changed_flag = True
                if changed_flag:
                    break  # restart outer while to rebuild fresh maps
            if changed_flag:
                continue

            # ── 6. Locking type 1 (Pointing) ─────────────────────────────────
            # Reuse reg_val: if all candidates for (region, val) lie in one
            # row or column, eliminate that val from the rest of the line.
            if reg_val is not None:
                for (_, v), cells in reg_val.items():
                    valid = [c for c in cells if c in cand_map and v in cand_map[c]]
                    if len(valid) < 2:
                        continue
                    rows_s = {r for r, _ in valid}
                    cols_s = {c for _, c in valid}
                    valid_set = set(valid)
                    if len(rows_s) == 1:
                        locked_row = next(iter(rows_s))
                        for c2 in range(size):
                            nb = (locked_row, c2)
                            if nb not in valid_set and nb in cand_map and v in cand_map[nb]:
                                cand_map[nb].discard(v)
                                trail.append((2, nb, v))
                                if not cand_map[nb]:
                                    return False
                                changed_flag = True
                    elif len(cols_s) == 1:
                        locked_col = next(iter(cols_s))
                        for r2 in range(size):
                            nb = (r2, locked_col)
                            if nb not in valid_set and nb in cand_map and v in cand_map[nb]:
                                cand_map[nb].discard(v)
                                trail.append((2, nb, v))
                                if not cand_map[nb]:
                                    return False
                                changed_flag = True
                if changed_flag:
                    continue

            # ── 7. Locking type 2 (Claiming) ─────────────────────────────────
            # Reuse row_val/col_val: if all row/col candidates for a value lie
            # in one region, eliminate that val from the rest of the region.
            if cell_region is not None and region_units is not None:
                for (_, v), cells in row_val.items():
                    valid = [c for c in cells if c in cand_map and v in cand_map[c]]
                    if len(valid) < 2:
                        continue
                    rids = {cell_region[nb] for nb in valid}
                    if len(rids) == 1:
                        rid = next(iter(rids))
                        valid_set = set(valid)
                        for nb in region_units[rid]:
                            if nb not in valid_set and nb in cand_map and v in cand_map[nb]:
                                cand_map[nb].discard(v)
                                trail.append((2, nb, v))
                                if not cand_map[nb]:
                                    return False
                                changed_flag = True
                if not changed_flag:
                    for (_, v), cells in col_val.items():
                        valid = [c for c in cells if c in cand_map and v in cand_map[c]]
                        if len(valid) < 2:
                            continue
                        rids = {cell_region[nb] for nb in valid}
                        if len(rids) == 1:
                            rid = next(iter(rids))
                            valid_set = set(valid)
                            for nb in region_units[rid]:
                                if nb not in valid_set and nb in cand_map and v in cand_map[nb]:
                                    cand_map[nb].discard(v)
                                    trail.append((2, nb, v))
                                    if not cand_map[nb]:
                                        return False
                                    changed_flag = True
                if changed_flag:
                    continue

            # ── 8. Naked pairs ─────────────────────────────────────────────────
            # Two cells in the same unit with identical 2-candidate sets: remove
            # those two values from every other cell in the unit.
            unit_dicts: list[dict] = [cells_by_row, cells_by_col]
            if cells_by_reg is not None:
                unit_dicts.append(cells_by_reg)
            for unit_dict in unit_dicts:
                for unit in unit_dict.values():
                    seen_pairs: dict[frozenset, tuple] = {}
                    for c in unit:
                        if c not in cand_map:
                            continue
                        cc = cand_map[c]
                        if len(cc) != 2:
                            continue
                        key = frozenset(cc)
                        if key in seen_pairs:
                            partner = seen_pairs[key]
                            pair_set = {c, partner}
                            for other in unit:
                                if other in pair_set or other not in cand_map:
                                    continue
                                for v in key:
                                    if v in cand_map[other]:
                                        cand_map[other].discard(v)
                                        trail.append((2, other, v))
                                        if not cand_map[other]:
                                            return False
                                        changed_flag = True
                        else:
                            seen_pairs[key] = c
            if changed_flag:
                continue

            return True  # stable – no technique found anything new

    def _count() -> int:
        if cancel_flag is not None and cancel_flag[0]:
            return 0
        if not cand_map:
            if constraint_ok is not None and not constraint_ok(grid):
                return 0
            return 1
        # MRV: branch on the cell with fewest candidates.
        best_cell = min(cand_map, key=lambda k: len(cand_map[k]))
        if not cand_map[best_cell]:
            return 0
        total = 0
        for val in list(cand_map[best_cell]):
            if best_cell not in cand_map or val not in cand_map[best_cell]:
                continue
            trail: list = []
            if _assign(best_cell, val, trail) and _propagate(trail):
                total += _count()
            _undo(trail)
            if total >= 2:
                break
        return total

    # Propagate the initial position, then count.
    trail0: list = []
    if not _propagate(trail0):
        _undo(trail0)
        return 0
    result = _count()
    _undo(trail0)
    return result


def _has_unique_solution(
    grid: Grid,
    size: int,
    symbols: list[int],
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]],
    cancel_flag: list[bool] | None = None,
    constraint_ok: Callable[[Grid], bool] | None = None,
    region_units: list[list[tuple[int, int]]] | None = None,
) -> bool:
    remaining = [(r, c) for r in range(size) for c in range(size) if grid[r][c] is None]
    return _count_solutions(grid, remaining, symbols, peer_cache, cancel_flag, constraint_ok, region_units) == 1


def check_unique(
    meta: VariantMetadata,
    board_state: list[list[int | None]],
    constraint_ok: Callable[[Grid], bool] | None = None,
    cancel_flag: list[bool] | None = None,
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]] | None = None,
    region_units: list[list[tuple[int, int]]] | None = None,
) -> bool:
    """Public uniqueness-check entry point for variant workers.

    Workers that bypass ``generate_puzzle`` (OneToTwentyFiveWorker,
    KenKenWorker, KakuroWorker, CodewordsWorker) call this to verify the
    generated puzzle has exactly one solution.

    Args:
        meta:          VariantMetadata supplying size, symbols, region_layout.
        board_state:   size×size grid of ints/None (puzzle with empties).
        constraint_ok: optional extra constraint callback (cage arithmetic etc.).
        cancel_flag:   single-element list; set [True] to request cancellation.
        peer_cache:    optional pre-built peer cache; pass this when calling
                       check_unique in a tight loop to avoid rebuilding the
                       cache (O(N⁴) for 25×25) on every iteration.
        region_units:  optional pre-built region units list; pass alongside
                       peer_cache to enable locking propagation for faster
                       uniqueness checking.

    Returns:
        True if exactly one solution exists, False otherwise.
    """
    size = meta.size
    if peer_cache is None:
        peer_cache = _build_peer_cache(
            size, meta.region_layout,
            has_box_regions=getattr(meta, "constraints", {}).get("has_box_regions", True),
        )
    if region_units is None:
        region_units = _build_region_units(size, meta.region_layout)
    grid: Grid = [list(row) for row in board_state]
    return _has_unique_solution(grid, size, list(meta.symbols), peer_cache, cancel_flag, constraint_ok, region_units)


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
    meta: object = None,
    constraint_ok: Callable[[Grid], bool] | None = None,
    cancel_flag: list[bool] | None = None,
) -> tuple[Grid, Grid]:
    """Generate a Sudoku puzzle together with its solution.

    Args:
        size: board dimension.
        region_layout: size×size mapping (row,col) -> region_id.
        symbols: allowed fill values.
        seed: RNG seed for reproducibility.
        difficulty: one of 'easy', 'medium', 'hard', 'expert'.
        meta: optional VariantMetadata; used for Str8ts/Killer special logic.
        constraint_ok: optional extra constraint checker passed to fill.
        cancel_flag: single-element list; set [True] to request cancellation.

    Returns:
        (puzzle, solution) where puzzle has None for empty cells and
        solution is the fully-filled grid.

    Raises:
        ValueError: for unrecognised difficulty.
        GenerationCancelled: if cancel_flag is set during generation.
    """
    if difficulty not in _DIFFICULTY_GIVENS:
        raise ValueError(
            f"Unknown difficulty {difficulty!r}. "
            f"Choose from {list(_DIFFICULTY_GIVENS)}."
        )

    rng = random.Random(seed)
    solution = generate_solution(
        size, region_layout, symbols, seed=seed,
        constraint_ok=constraint_ok, cancel_flag=cancel_flag,
    )
    peer_cache = _build_peer_cache(size, region_layout)
    target_givens = _DIFFICULTY_GIVENS[difficulty]

    # --- Variant-specific pre-processing ---
    empties_override: set[tuple[int, int]] | None = None
    _str8ts_black_set: set[tuple[int, int]] = set()
    if meta is not None:
        constraints = getattr(meta, "constraints", {})
        meta_name = getattr(meta, "name", None)

        # --- Killer: DC2 difficulty-based fixed-cell population ---
        if constraints.get("cages") is not None:
            puzzle: Grid = [[None] * size for _ in range(size)]
            cages = constraints["cages"]
            sorted_cages = sorted(cages, key=lambda cg: len(cg.get("cells", [])))
            if difficulty == "easy":
                for cage in sorted_cages:
                    if len(cage.get("cells", [])) == 1:
                        r, c = int(cage["cells"][0][0]), int(cage["cells"][0][1])
                        puzzle[r][c] = solution[r][c]
            elif difficulty == "medium":
                cutoff = max(1, int(len(sorted_cages) * 0.3))
                for cage in sorted_cages[:cutoff]:
                    for cell_entry in cage.get("cells", []):
                        r, c = int(cell_entry[0]), int(cell_entry[1])
                        puzzle[r][c] = solution[r][c]
            # Hard / Expert: puzzle stays all-None
            return puzzle, solution

        # --- Str8ts: DC1 density-preserving target + DC3 black-cell exposure ---
        if constraints.get("black_cells") is not None:
            bc_list = sorted((int(p[0]), int(p[1])) for p in constraints["black_cells"])
            black_set_local = set(bc_list)
            _str8ts_black_set = black_set_local
            white_count = size * size - len(bc_list)
            # DC1: density-preserving clue count scaled from 9×9 baseline
            target_givens = int(white_count * _DIFFICULTY_GIVENS[difficulty] / 81)
            # Only white cells are candidates for clue removal
            empties_override = {
                (r, c)
                for r in range(size)
                for c in range(size)
                if (r, c) not in black_set_local
            }

    # Start from the full solution; remove cells one at a time
    puzzle = [row[:] for row in solution]
    if empties_override is not None:
        all_cells = list(empties_override)
    else:
        all_cells = [(r, c) for r in range(size) for c in range(size)]
    rng.shuffle(all_cells)

    filled = size * size
    for row, col in all_cells:
        if cancel_flag is not None and cancel_flag[0]:
            raise GenerationCancelled()
        if filled <= target_givens:
            break
        saved = puzzle[row][col]
        puzzle[row][col] = None
        if _has_unique_solution(puzzle, size, symbols, peer_cache, cancel_flag, constraint_ok):
            filled -= 1
        else:
            puzzle[row][col] = saved  # restore – removal broke uniqueness

    # --- Post-validate Str8ts consecutiveness (up to 50 retries in caller) ---
    # (At this layer we just return; the caller in variant_registry handles retries.)

    # --- DC3: Str8ts black-cell digit exposure ---
    if _str8ts_black_set:
        bc_list_sorted = sorted(_str8ts_black_set)
        if difficulty == "easy":
            exposed_bc: set[tuple[int, int]] = set(bc_list_sorted)
        elif difficulty == "medium":
            exposure_count = int(
                len(bc_list_sorted) * _DIFFICULTY_GIVENS["medium"] / _DIFFICULTY_GIVENS["easy"]
            )
            shuffled_bc = list(bc_list_sorted)
            rng.shuffle(shuffled_bc)
            exposed_bc = set(shuffled_bc[:exposure_count])
        else:  # hard / expert
            exposed_bc = set()
        # Update meta.constraints["black_givens"] so the controller can read them
        black_givens_new = [
            [r, c, solution[r][c]] for r, c in sorted(exposed_bc)
        ]
        if hasattr(meta, "constraints"):
            meta.constraints["black_givens"] = black_givens_new  # type: ignore[union-attr]
        # Clear non-exposed black cells from the puzzle (they started as solution values)
        for r, c in _str8ts_black_set:
            if (r, c) not in exposed_bc:
                puzzle[r][c] = None

    if cancel_flag is not None and cancel_flag[0]:
        raise GenerationCancelled()

    return puzzle, solution
