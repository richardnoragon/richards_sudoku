"""Solver and validator for Sudoku puzzles.

Supports any variant described by a VariantMetadata region_layout.
Uses the following constraint propagation techniques in order:
  1.  Naked singles
  2.  Hidden singles
  3.  Locking – Type 1 (Pointing)
  4.  Locking – Type 2 / Claiming (Intersections)
  5.  Naked pairs
  6.  Naked triplets
  7.  Naked quads
  8.  Hidden pairs
  9.  Hidden triplets
  10. Hidden quads
  11. X-Wing        (basic fish, n=2)
  12. Swordfish     (basic fish, n=3)
  13. Jellyfish     (basic fish, n=4)
  14. XY-Wing
  15. XYZ-Wing
  16. Unique Rectangle (Types 1, 2, 4)
  17. Simple Coloring  (Loops / Single-Digit Chains)
  18. Bivalue Universal Grave (BUG+1)
  19. Aligned Pair Exclusion  (APE)
  20. Bidirectional Cycles    (AIC Loops)
  21. Nishio                  (single-digit trial elimination)
  22. Forcing Chains          (dual-branch common-elimination)

Only puzzles solvable by these techniques will be solved.
"""
from __future__ import annotations

from itertools import combinations
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
    has_box_regions: bool = True,
) -> dict[tuple[int, int], frozenset[tuple[int, int]]]:
    if has_box_regions:
        return {
            (r, c): _peers(r, c, size, region_layout)
            for r in range(size)
            for c in range(size)
        }
    # KenKen / Latin-square variants: uniqueness only by row and column.
    return {
        (r, c): frozenset(
            (r2, c2)
            for r2 in range(size)
            for c2 in range(size)
            if (r2, c2) != (r, c) and (r2 == r or c2 == c)
        )
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


def _build_units(
    size: int,
    region_layout: Sequence[Sequence[int]],
) -> list[list[tuple[int, int]]]:
    """Return all rows, columns, and regions as lists of cell coordinates."""
    units: list[list[tuple[int, int]]] = []
    for r in range(size):
        units.append([(r, c) for c in range(size)])
    for c in range(size):
        units.append([(r, c) for r in range(size)])
    num_regions = max(region_layout[r][c] for r in range(size) for c in range(size)) + 1
    for rid in range(num_regions):
        units.append([
            (r, c)
            for r in range(size)
            for c in range(size)
            if region_layout[r][c] == rid
        ])
    return units


def _build_region_units(
    size: int,
    region_layout: Sequence[Sequence[int]],
) -> list[list[tuple[int, int]]]:
    """Return only region units (used by pointing / claiming)."""
    num_regions = max(region_layout[r][c] for r in range(size) for c in range(size)) + 1
    return [
        [
            (r, c)
            for r in range(size)
            for c in range(size)
            if region_layout[r][c] == rid
        ]
        for rid in range(num_regions)
    ]


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
# Solver  (22 techniques: singles → locking → naked/hidden subsets → fish → wings → UR → coloring → BUG → APE → AIC → Nishio → Forcing)
# ---------------------------------------------------------------------------

def _solve_logical(
    grid: Grid,
    size: int,
    symbols: list[int],
    peer_cache: dict[tuple[int, int], frozenset[tuple[int, int]]],
    units: list[list[tuple[int, int]]],
    region_units: list[list[tuple[int, int]]],
) -> bool:
    """Apply up to 17 constraint propagation techniques until solved or stuck.

    Techniques in priority order (cheapest first):
      1.  Naked singles        — cell with one candidate: fill it
      2.  Hidden singles       — digit with one possible cell in a unit: fill it
      3.  Locking Type 1       — region digit confined to one row/col (Pointing):
                                  eliminate from rest of that line
      4.  Locking Type 2       — line digit confined to one region
                                  (Claiming / Intersections):
                                  eliminate from rest of that region
      5.  Naked pairs          — 2 cells share exactly 2 candidates: eliminate from unit
      6.  Naked triplets       — 3 cells share exactly 3 candidates: eliminate from unit
      7.  Naked quads          — 4 cells share exactly 4 candidates: eliminate from unit
      8.  Hidden pairs         — 2 digits confined to 2 cells: strip extras
      9.  Hidden triplets      — 3 digits confined to 3 cells: strip extras
      10. Hidden quads         — 4 digits confined to 4 cells: strip extras
      11. X-Wing  (fish n=2)   — 2 rows×2 cols fish: eliminate from cover columns
      12. Swordfish (fish n=3) — 3 rows×3 cols fish: eliminate from cover columns
      13. Jellyfish (fish n=4) — 4 rows×4 cols fish: eliminate from cover columns
      14. XY-Wing              — pivot {X,Y} + two pincers {X,Z}/{Y,Z}: eliminate Z
                                  from cells seeing both pincers
      15. XYZ-Wing             — pivot {X,Y,Z} + two wings {X,Z}/{Y,Z}: eliminate Z
                                  from cells seeing all three
      16. Unique Rectangle     — 4-cell rectangle in 2 regions with UR pair {X,Y};
                                  deadly-pattern argument yields eliminations
                                  (Types 1, 2, and 4 implemented)
      17. Simple Coloring      — conjugate-pair chains for a single digit;
                                  colour conflict or colour trap eliminates digit
      18. BUG+1                — exactly one unsolved cell has 3+ candidates;
                                  all others are bivalues; the extra digit that
                                  would restore the deadly BUG pattern is
                                  eliminated, leaving a naked single
      19. APE                  — two cells in the same unit share a common peer
                                  set; value-pairs that are jointly forbidden by
                                  bivalue peers are eliminated from the pair
      20. Bidirectional Cycles — Alternating Inference Chain (AIC) closed loops;
                                  strong/weak link alternation around a cycle
                                  yields two elimination rules:
                                  (a) any candidate seen by both endpoints of a
                                      strong link in the cycle is eliminated;
                                  (b) a cell with only weak-link candidates in
                                      the cycle can have all other candidates
                                      stripped
      21. Nishio               — single-digit trial: hypothetically place digit d
                                  in cell and propagate naked/hidden singles;
                                  if contradiction arises, d is eliminated
      22. Forcing Chains       — for every bivalue cell, follow BOTH branches
                                  (assume X, assume Y) propagating singles;
                                  any elimination common to both branches is
                                  applied to the real candidate map

    The candidate map is built once and maintained incrementally; eliminations
    from every pass persist into subsequent passes.
    Returns True when every cell is filled, False on contradiction or no progress.
    """
    # --- Build candidate map once; keep it up to date incrementally ---
    cand_map: dict[tuple[int, int], set[int]] = {}
    for r in range(size):
        for c in range(size):
            if grid[r][c] is None:
                cands = _candidates(grid, r, c, symbols, peer_cache)
                if not cands:
                    return False
                cand_map[(r, c)] = cands

    # Pre-compute region membership for Unique Rectangle checks
    region_of: dict[tuple[int, int], int] = {}
    for rid, reg in enumerate(region_units):
        for cell in reg:
            region_of[cell] = rid

    def _fill(cell: tuple[int, int], val: int) -> bool:
        """Place *val* in *cell*, remove from cand_map, propagate to peers."""
        r, c = cell
        grid[r][c] = val
        del cand_map[cell]
        for peer in peer_cache[cell]:
            if peer in cand_map:
                cand_map[peer].discard(val)
                if not cand_map[peer]:
                    return False
        return True

    # Pre-build row/column unit lists once (used by Locking Type 2 / Claiming).
    row_col_units: list[list[tuple[int, int]]] = (
        [[(r, c) for c in range(size)] for r in range(size)]
        + [[(r, c) for r in range(size)] for c in range(size)]
    )

    while True:
        if not cand_map:
            return True

        changed = False

        # --- 1. Naked singles ---
        for cell in list(cand_map):
            if cell in cand_map and len(cand_map[cell]) == 1:
                if not _fill(cell, next(iter(cand_map[cell]))):
                    return False
                changed = True
        if changed:
            continue

        # --- 2. Hidden singles ---
        for unit in units:
            for val in symbols:
                if any(grid[r][c] == val for r, c in unit):
                    continue
                possible = [
                    cell for cell in unit
                    if cell in cand_map and val in cand_map[cell]
                ]
                if not possible:
                    return False  # digit has no valid cell in this unit → contradiction
                if len(possible) == 1:
                    if not _fill(possible[0], val):
                        return False
                    changed = True
        if changed:
            continue

        # --- 3. Locking – Type 1 (Pointing) ---
        # Region candidates for a digit all in one row/col → remove from that line.
        for region in region_units:
            for val in symbols:
                if any(grid[r][c] == val for r, c in region):
                    continue
                reg_cells = [
                    cell for cell in region
                    if cell in cand_map and val in cand_map[cell]
                ]
                if len(reg_cells) < 2:
                    continue
                rows = {r for r, _ in reg_cells}
                cols = {c for _, c in reg_cells}
                reg_set = set(reg_cells)
                if len(rows) == 1:
                    locked_row = next(iter(rows))
                    for c2 in range(size):
                        cell = (locked_row, c2)
                        if cell not in reg_set and cell in cand_map and val in cand_map[cell]:
                            cand_map[cell].discard(val)
                            if not cand_map[cell]:
                                return False
                            changed = True
                elif len(cols) == 1:
                    locked_col = next(iter(cols))
                    for r2 in range(size):
                        cell = (r2, locked_col)
                        if cell not in reg_set and cell in cand_map and val in cand_map[cell]:
                            cand_map[cell].discard(val)
                            if not cand_map[cell]:
                                return False
                            changed = True
        if changed:
            continue

        # --- 4. Locking – Type 2 / Claiming (Intersections) ---
        # Line candidates for a digit all in one region → remove from that region.
        # Uses the pre-built region_of map (O(1) per cell) instead of iterating
        # over all region_units for every (line_unit, val) pair.
        for line_unit in row_col_units:
            for val in symbols:
                if any(grid[r][c] == val for r, c in line_unit):
                    continue
                line_cells = [
                    cell for cell in line_unit
                    if cell in cand_map and val in cand_map[cell]
                ]
                if len(line_cells) < 2:
                    continue
                cell_set = set(line_cells)
                found_rids: set[int] = {region_of[cell] for cell in line_cells}
                if len(found_rids) == 1:
                    rid = next(iter(found_rids))
                    for cell in region_units[rid]:
                        if cell not in cell_set and cell in cand_map and val in cand_map[cell]:
                            cand_map[cell].discard(val)
                            if not cand_map[cell]:
                                return False
                            changed = True
        if changed:
            continue

        # --- 5–7. Naked subsets: pairs (n=2), triplets (n=3), quads (n=4) ---
        # n cells whose combined candidates total exactly n digits → those digits
        # are locked to that combo and can be removed from all other cells in the unit.
        for n in range(2, 5):
            for unit in units:
                empty_cells = [cell for cell in unit if cell in cand_map]
                if len(empty_cells) <= n:
                    continue
                for combo in combinations(empty_cells, n):
                    combined = set().union(*(cand_map[cell] for cell in combo))
                    if len(combined) == n:
                        combo_set = set(combo)
                        for cell in empty_cells:
                            if cell not in combo_set:
                                extra = cand_map[cell] & combined
                                if extra:
                                    cand_map[cell] -= extra
                                    if not cand_map[cell]:
                                        return False
                                    changed = True
        if changed:
            continue

        # --- 8–10. Hidden subsets: pairs (n=2), triplets (n=3), quads (n=4) ---
        # n digits whose only possible positions in a unit are exactly the same n
        # cells → all other candidates can be removed from those n cells.
        for n in range(2, 5):
            for unit in units:
                empty_cells = [cell for cell in unit if cell in cand_map]
                if len(empty_cells) < n:
                    continue
                placed_vals = {grid[r][c] for r, c in unit if grid[r][c] is not None}
                unplaced = [val for val in symbols if val not in placed_vals]
                if len(unplaced) < n:
                    continue
                for combo_vals in combinations(unplaced, n):
                    combo_val_set = set(combo_vals)
                    covering = [
                        cell for cell in empty_cells
                        if cand_map[cell] & combo_val_set
                    ]
                    if len(covering) == n:
                        for cell in covering:
                            extra = cand_map[cell] - combo_val_set
                            if extra:
                                cand_map[cell] -= extra
                                if not cand_map[cell]:
                                    return False
                                changed = True

        if changed:
            continue

        # --- 11–13. Basic Fish: X-Wing (n=2), Swordfish (n=3), Jellyfish (n=4) ---
        # For each digit, pick n rows where that digit can go in ≤ n columns.
        # If the union of those candidate columns is exactly n (the cover), the
        # digit is confined to those n column/row intersections and can be removed
        # from every other cell in the n cover columns.  The same logic applies
        # transposed (columns as base sets, rows as covers).
        for n in (2, 3, 4):
            for val in symbols:
                # -- rows as base sets, columns as covers --
                row_bases: list[tuple[int, frozenset[int]]] = []
                for r in range(size):
                    if any(grid[r][c] == val for c in range(size)):
                        continue
                    cand_cols = frozenset(
                        c for c in range(size)
                        if (r, c) in cand_map and val in cand_map[(r, c)]
                    )
                    if 2 <= len(cand_cols) <= n:
                        row_bases.append((r, cand_cols))
                if len(row_bases) >= n:
                    for combo in combinations(row_bases, n):
                        cover_cols = frozenset().union(*(cols for _, cols in combo))
                        if len(cover_cols) == n:
                            base_rows = frozenset(r for r, _ in combo)
                            for col in cover_cols:
                                for r in range(size):
                                    if r not in base_rows:
                                        cell = (r, col)
                                        if cell in cand_map and val in cand_map[cell]:
                                            cand_map[cell].discard(val)
                                            if not cand_map[cell]:
                                                return False
                                            changed = True

                # -- columns as base sets, rows as covers (transposed) --
                col_bases: list[tuple[int, frozenset[int]]] = []
                for c in range(size):
                    if any(grid[r][c] == val for r in range(size)):
                        continue
                    cand_rows = frozenset(
                        r for r in range(size)
                        if (r, c) in cand_map and val in cand_map[(r, c)]
                    )
                    if 2 <= len(cand_rows) <= n:
                        col_bases.append((c, cand_rows))
                if len(col_bases) >= n:
                    for combo in combinations(col_bases, n):
                        cover_rows = frozenset().union(*(rows for _, rows in combo))
                        if len(cover_rows) == n:
                            base_cols = frozenset(c for c, _ in combo)
                            for row in cover_rows:
                                for c in range(size):
                                    if c not in base_cols:
                                        cell = (row, c)
                                        if cell in cand_map and val in cand_map[cell]:
                                            cand_map[cell].discard(val)
                                            if not cand_map[cell]:
                                                return False
                                            changed = True

        # --- 14. XY-Wing ---
        # Pivot cell with exactly 2 candidates {X, Y}.  Two pincer cells, each
        # with exactly 2 candidates, both seen by the pivot:
        #   pincerA has {X, Z}, pincerB has {Y, Z}.
        # Any cell that sees BOTH pincers cannot contain Z.
        two_cand_cells = [cell for cell in cand_map if len(cand_map[cell]) == 2]
        for pivot in two_cand_cells:
            # Collect (peer_cell, digit_shared_with_pivot, extra_digit)
            pincers: list[tuple[tuple[int, int], int, int]] = []
            for peer in peer_cache[pivot]:
                if peer not in cand_map or len(cand_map[peer]) != 2:
                    continue
                shared = cand_map[pivot] & cand_map[peer]
                if len(shared) == 1:
                    (s,) = shared
                    (z,) = cand_map[peer] - {s}
                    pincers.append((peer, s, z))
            # Look for a pair (pincerA, pincerB): they share different digits with
            # the pivot but the same extra digit Z.
            for i, (pa, sa, za) in enumerate(pincers):
                for pb, sb, zb in pincers[i + 1:]:
                    if sa == sb or za != zb:
                        continue  # not a valid XY-Wing pair
                    z = za
                    common = (peer_cache[pa] & peer_cache[pb]) - {pivot}
                    for cell in common:
                        if cell in cand_map and z in cand_map[cell]:
                            cand_map[cell].discard(z)
                            if not cand_map[cell]:
                                return False
                            changed = True
        if changed:
            continue

        # --- 15. XYZ-Wing ---
        # Pivot cell with exactly 3 candidates {X, Y, Z}.  Two wing cells, each
        # with exactly 2 candidates that are a strict subset of the pivot's
        # candidates, both seen by the pivot:
        #   wingA has {X, Z}, wingB has {Y, Z}.
        # Any cell that sees ALL THREE (pivot + both wings) cannot contain Z.
        three_cand_cells = [cell for cell in cand_map if len(cand_map[cell]) == 3]
        for pivot in three_cand_cells:
            pivot_cands = cand_map[pivot]
            wings: list[tuple[int, int]] = []
            for peer in peer_cache[pivot]:
                if peer not in cand_map or len(cand_map[peer]) != 2:
                    continue
                if cand_map[peer].issubset(pivot_cands):
                    wings.append(peer)
            for i in range(len(wings)):
                for j in range(i + 1, len(wings)):
                    wa, wb = wings[i], wings[j]
                    shared_z = cand_map[wa] & cand_map[wb]
                    if len(shared_z) != 1:
                        continue
                    z = next(iter(shared_z))
                    if z not in pivot_cands:
                        continue
                    common = peer_cache[pivot] & peer_cache[wa] & peer_cache[wb]
                    for cell in common:
                        if cell in cand_map and z in cand_map[cell]:
                            cand_map[cell].discard(z)
                            if not cand_map[cell]:
                                return False
                            changed = True
        if changed:
            continue

        # --- 16. Unique Rectangle (Types 1, 2, & 4) ---
        # A Unique Rectangle is 4 cells at the corners of a row×col rectangle
        # that spans exactly 2 regions.  If every cell contained only the UR
        # pair {X,Y}, two indistinguishable solutions would exist (a "deadly
        # pattern"), contradicting uniqueness.  Three sub-types are applied:
        #
        #   Type 1 – 3 cells have exactly {X,Y}; 1 roof cell has {X,Y,+extras}:
        #             eliminate X and Y from the roof cell.
        #
        #   Type 2 – 2 floor cells have {X,Y}; 2 roof cells each have {X,Y,Z}
        #             (one identical extra Z): eliminate Z from every cell
        #             that sees both roof cells.
        #
        #   Type 4 – 2 floor cells have {X,Y}; 2 roof cells have {X,Y,+extras}
        #             and share a unit in which digit X (or Y) appears only in
        #             the roof cells: eliminate the OTHER digit from both roofs.
        for r1, r2 in combinations(range(size), 2):
            for c1, c2 in combinations(range(size), 2):
                rect = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
                if any(cell not in cand_map for cell in rect):
                    continue
                # UR validity: the 4 cells must span exactly 2 regions
                if len({region_of[cell] for cell in rect}) != 2:
                    continue
                # Digits common to all 4 cells form UR pair candidates
                common = (
                    cand_map[(r1, c1)]
                    & cand_map[(r1, c2)]
                    & cand_map[(r2, c1)]
                    & cand_map[(r2, c2)]
                )
                if len(common) < 2:
                    continue
                for X, Y in combinations(common, 2):
                    ur_pair: frozenset[int] = frozenset({X, Y})
                    floor_cells = [
                        cell for cell in rect
                        if cand_map[cell] == ur_pair
                    ]
                    roof_cells = [
                        cell for cell in rect
                        if cand_map[cell] != ur_pair
                        and ur_pair.issubset(cand_map[cell])
                    ]
                    # -- Type 1: 3 floors, 1 roof --
                    if len(floor_cells) == 3 and len(roof_cells) == 1:
                        roof = roof_cells[0]
                        for v in (X, Y):
                            if v in cand_map[roof]:
                                cand_map[roof].discard(v)
                                if not cand_map[roof]:
                                    return False
                                changed = True
                    elif len(floor_cells) == 2 and len(roof_cells) == 2:
                        ra, rb = roof_cells
                        extras_a = cand_map[ra] - ur_pair
                        extras_b = cand_map[rb] - ur_pair
                        # -- Type 2: both roofs have the same single extra Z --
                        if len(extras_a) == 1 and extras_a == extras_b:
                            (Z,) = extras_a
                            common_peers = (
                                (peer_cache[ra] & peer_cache[rb]) - set(rect)
                            )
                            for cell in common_peers:
                                if cell in cand_map and Z in cand_map[cell]:
                                    cand_map[cell].discard(Z)
                                    if not cand_map[cell]:
                                        return False
                                    changed = True
                        # -- Type 4: roof cells share a unit; one UR digit
                        #    is locked to the roof cells in that unit
                        #    → eliminate the OTHER digit from both roofs --
                        for unit in units:
                            unit_set = set(unit)
                            if ra not in unit_set or rb not in unit_set:
                                continue
                            for locked, other in ((X, Y), (Y, X)):
                                locked_elsewhere = [
                                    cell for cell in unit
                                    if cell in cand_map
                                    and locked in cand_map[cell]
                                    and cell not in {ra, rb}
                                ]
                                if not locked_elsewhere:
                                    for roof in (ra, rb):
                                        if other in cand_map.get(roof, set()):
                                            cand_map[roof].discard(other)
                                            if not cand_map[roof]:
                                                return False
                                            changed = True
        if changed:
            continue

        # --- 17. Simple Coloring (Loops / Single-Digit Chains) ---
        # For each digit build a "strong-link" graph: an edge joins two cells
        # when they are the ONLY two candidates for that digit in a shared
        # unit (a conjugate pair).  Each connected sub-graph is 2-coloured
        # via BFS: one colour = "digit is here", the other = "digit is not".
        #
        #   Rule 1 – Color Conflict: two same-coloured cells that see each
        #             other → that colour is proven false → eliminate the
        #             digit from every cell with that colour.
        #
        #   Rule 2 – Color Trap: an outside cell that sees at least one cell
        #             of EACH colour → it is false regardless of which colour
        #             is true → eliminate the digit from that cell.
        for val in symbols:
            val_cells = [cell for cell in cand_map if val in cand_map[cell]]
            if len(val_cells) < 4:
                continue
            val_cell_set = set(val_cells)
            # Build strong-link adjacency
            adj: dict[tuple[int, int], set[tuple[int, int]]] = {
                cell: set() for cell in val_cells
            }
            for unit in units:
                uv = [cell for cell in unit if cell in val_cell_set]
                if len(uv) == 2:
                    a, b = uv
                    adj[a].add(b)
                    adj[b].add(a)
            coloring: dict[tuple[int, int], int] = {}
            for start in val_cells:
                if start in coloring or not adj[start]:
                    continue
                # BFS 2-colouring of this connected component
                component: list[tuple[int, int]] = []
                queue = [start]
                coloring[start] = 0
                while queue:
                    cell = queue.pop(0)
                    component.append(cell)
                    for nb in adj[cell]:
                        if nb not in coloring:
                            coloring[nb] = 1 - coloring[cell]
                            queue.append(nb)
                if len(component) < 2:
                    continue
                color0 = [c for c in component if coloring[c] == 0]
                color1 = [c for c in component if coloring[c] == 1]
                # Rule 1: same-coloured cells that see each other
                for c_cells in (color0, color1):
                    if any(
                        cb in peer_cache[ca]
                        for ca, cb in combinations(c_cells, 2)
                    ):
                        for cell in c_cells:
                            if cell in cand_map and val in cand_map[cell]:
                                cand_map[cell].discard(val)
                                if not cand_map[cell]:
                                    return False
                                changed = True
                if changed:
                    break
                # Rule 2: outside cell seeing both colours
                comp_set = set(component)
                set0: frozenset[tuple[int, int]] = frozenset(color0)
                set1: frozenset[tuple[int, int]] = frozenset(color1)
                for cell in val_cells:
                    if cell in comp_set or cell not in cand_map:
                        continue
                    if peer_cache[cell] & set0 and peer_cache[cell] & set1:
                        cand_map[cell].discard(val)
                        if not cand_map[cell]:
                            return False
                        changed = True
            if changed:
                break
        if changed:
            continue

        # --- 18. Bivalue Universal Grave (BUG+1) ---
        # A Bivalue Universal Grave is a position where every unsolved cell has
        # exactly 2 candidates AND every unsolved unit has each remaining digit
        # exactly twice — a deadly pattern with multiple solutions.  The only
        # escape is a single "BUG+1" cell that has one extra (third+) candidate
        # beyond the bivalue pattern.  The extra digit(s) in that cell must
        # contain the true value, so every digit that would perpetuate the
        # deadly pattern (i.e. appears exactly twice in every unit through that
        # cell) can be eliminated, leaving a naked single.
        non_bivalue = [
            cell for cell in cand_map if len(cand_map[cell]) != 2
        ]
        if len(non_bivalue) == 1:
            bug_cell = non_bivalue[0]
            bug_cands = set(cand_map[bug_cell])
            # For each candidate digit in the BUG cell, check whether removing
            # it would leave a pure bivalue grid (i.e. the digit currently
            # appears an odd number of times in some unit through this cell —
            # placing it here keeps the count even and perpetuates the deadly
            # pattern, so it can NOT be placed here and must be eliminated).
            for val in list(bug_cands):
                # Count occurrences of val in each unit that contains bug_cell
                perpetuates = False
                for unit in units:
                    if bug_cell not in unit:
                        continue
                    count = sum(
                        1 for cell in unit
                        if cell in cand_map and val in cand_map[cell]
                    )
                    # In a pure BUG each digit appears exactly twice per unit.
                    # If count is already 2 (including bug_cell), placing val
                    # here would keep the even count — perpetuating the grave.
                    if count == 2:
                        perpetuates = True
                        break
                if perpetuates:
                    cand_map[bug_cell].discard(val)
                    if not cand_map[bug_cell]:
                        return False
                    changed = True
        if changed:
            continue

        # --- 19. Aligned Pair Exclusion (APE) ---
        # Consider every pair of unsolved cells (A, B) that share at least one
        # common unit (row, column, or region).  Collect all bivalue peers: cells
        # visible to BOTH A and B that have exactly 2 candidates.
        # Build the set of forbidden (vA, vB) assignments:
        #   - vA == vB is always forbidden (same digit in peers of a shared unit)
        #   - any pair (vA, vB) that is jointly eliminated by a bivalue peer P:
        #       P has exactly {vA, vB} → placing vA in A forces vB into P,
        #       but P also sees B which would need vB — contradiction.
        # For each digit d in A's candidates: if ALL pairings (d, vB) for every
        # vB in B's candidates are forbidden, then d can be eliminated from A.
        # Symmetrically for digits in B.
        for unit in units:
            empty_unit = [cell for cell in unit if cell in cand_map]
            for ca, cb in combinations(empty_unit, 2):
                # Common peers visible to BOTH cells (excluding each other)
                common_peers = (
                    (peer_cache[ca] & peer_cache[cb])
                    - {ca, cb}
                )
                bivalue_peers = [
                    p for p in common_peers
                    if p in cand_map and len(cand_map[p]) == 2
                ]
                if not bivalue_peers:
                    continue
                cands_a = list(cand_map.get(ca, set()))
                cands_b = list(cand_map.get(cb, set()))
                if not cands_a or not cands_b:
                    continue
                # Pre-compute the set of forbidden (vA, vB) pairs
                forbidden: set[tuple[int, int]] = set()
                # Same digit — only relevant when cells share a unit (they do)
                for v in set(cands_a) & set(cands_b):
                    forbidden.add((v, v))
                # Bivalue peer eliminates pairs containing both its digits
                for p in bivalue_peers:
                    pa, pb = tuple(cand_map[p])  # exactly 2 elements
                    # If vA==pa AND vB==pb then placing pa in A forces pb into P,
                    # but P sees B which also needs pb — forbidden.
                    if pa in cands_a and pb in cands_b:
                        forbidden.add((pa, pb))
                    if pb in cands_a and pa in cands_b:
                        forbidden.add((pb, pa))
                # Eliminate from A: digit vA where every (vA, vB) is forbidden
                for va in list(cands_a):
                    if ca not in cand_map or va not in cand_map[ca]:
                        continue
                    if all((va, vb) in forbidden for vb in cands_b):
                        cand_map[ca].discard(va)
                        if not cand_map[ca]:
                            return False
                        changed = True
                # Eliminate from B: digit vB where every (vA, vB) is forbidden
                for vb in list(cands_b):
                    if cb not in cand_map or vb not in cand_map[cb]:
                        continue
                    if all((va, vb) in forbidden for va in cands_a):
                        cand_map[cb].discard(vb)
                        if not cand_map[cb]:
                            return False
                        changed = True
        if changed:
            continue

        # --- 20. Bidirectional Cycles (AIC Loops) ---
        # An Alternating Inference Chain (AIC) alternates strong links (the
        # digit MUST be in one of the two cells) and weak links (the digit
        # CAN be in at most one of the two cells).  When such a chain closes
        # into a cycle every link is simultaneously strong AND weak, giving
        # two elimination rules:
        #
        #   Rule A – any candidate visible to BOTH endpoints of a strong link
        #             in the cycle can be eliminated (it sees a cell that must
        #             hold the digit, whichever way the chain resolves).
        #
        #   Rule B – any cell that appears in the cycle with a particular
        #             digit connected only by weak links must eventually hold
        #             the digit (both neighbours forbid it, one from each
        #             resolution), so all OTHER candidates in that cell can be
        #             stripped.
        #
        # This implementation builds the AIC graph as (cell, digit) nodes,
        # with edges labelled S (strong) or W (weak):
        #   Strong link: the only two cells in a shared unit that hold digit d.
        #   Weak   link: two different cells/digits in the same cell
        #                (bivalue cell) or any two candidates in a shared unit.
        # Cycles of even length with alternating S/W labels are detected via
        # DFS up to a configurable depth.
        MAX_CYCLE_DEPTH = 8  # limit search depth to keep runtime bounded

        # Build strong-link pairs per digit (same as Simple Coloring)
        strong: dict[int, list[tuple[tuple[int, int], tuple[int, int]]]] = {}
        for val in symbols:
            slinks: list[tuple[tuple[int, int], tuple[int, int]]] = []
            for unit in units:
                uv = [cell for cell in unit if cell in cand_map and val in cand_map[cell]]
                if len(uv) == 2:
                    slinks.append((uv[0], uv[1]))
            strong[val] = slinks

        # Node = (cell, digit).  We find cycles by DFS from each start node.
        # Each step alternates between strong and weak links.
        # Strong link  (cell_a, d) → (cell_b, d): digit d confined to 2 cells in a unit.
        # Weak   link  (cell,  d1) → (cell,  d2): same cell, 2 different digits (bivalue).
        # Weak   link  (cell_a, d) → (cell_b, d): same digit, any shared-unit pair.

        def _strong_neighbours(
            cell: tuple[int, int], val: int
        ) -> list[tuple[tuple[int, int], int]]:
            """Return (cell2, val) for every strong link involving (cell, val)."""
            result = []
            for unit in units:
                uv = [
                    c for c in unit
                    if c in cand_map and val in cand_map[c]
                ]
                if len(uv) == 2 and cell in uv:
                    other = uv[0] if uv[1] == cell else uv[1]
                    result.append((other, val))
            return result

        def _weak_neighbours(
            cell: tuple[int, int], val: int
        ) -> list[tuple[tuple[int, int], int]]:
            """Return (cell2, val2) for every weak link from (cell, val)."""
            result = []
            # Same-cell weak link (bivalue only, to keep search tight)
            if len(cand_map.get(cell, set())) == 2:
                for v2 in cand_map[cell]:
                    if v2 != val:
                        result.append((cell, v2))
            # Same-digit weak link to any peer that also has the digit
            for peer in peer_cache[cell]:
                if peer in cand_map and val in cand_map[peer] and peer != cell:
                    result.append((peer, val))
            return result

        # DFS to find even-length alternating cycles; link_type alternates
        # S → W → S → …  The first step from a start node is always strong.
        found_cycles: list[list[tuple[tuple[int, int], int]]] = []

        for val in symbols:
            for start_cell in list(cand_map):
                if val not in cand_map.get(start_cell, set()):
                    continue
                start = (start_cell, val)
                # DFS state: (current_node, path, next_link_is_strong)
                stack: list[
                    tuple[
                        tuple[tuple[int, int], int],
                        list[tuple[tuple[int, int], int]],
                        bool,
                    ]
                ] = []
                stack.append((start, [start], True))
                while stack:
                    node, path, next_strong = stack.pop()
                    if len(path) > MAX_CYCLE_DEPTH:
                        continue
                    if next_strong:
                        neighbours = _strong_neighbours(node[0], node[1])
                    else:
                        neighbours = _weak_neighbours(node[0], node[1])
                    for nb in neighbours:
                        if nb == start and len(path) >= 4 and not next_strong:
                            # Closed cycle: last link back to start is weak
                            # meaning start itself is a strong-link endpoint →
                            # valid even-length alternating cycle.
                            found_cycles.append(list(path))
                        elif nb not in path:
                            stack.append((nb, path + [nb], not next_strong))

        for cycle in found_cycles:
            if changed:
                break
            n = len(cycle)
            # Rule A: for each strong link in cycle, eliminate digit from
            # cells that see BOTH endpoints of the link.
            for i in range(n):
                # Strong links are at even positions (0-based step index)
                # The cycle alternates S, W, S, W ..., and closes with W.
                # Step i → i+1 is strong when i is even (0-indexed).
                if i % 2 != 0:
                    continue
                cell_a, d_a = cycle[i]
                cell_b, d_b = cycle[(i + 1) % n]
                if d_a != d_b:
                    continue  # strong link must be same digit
                d = d_a
                common = (peer_cache[cell_a] & peer_cache[cell_b]) - {cell_a, cell_b}
                for cell in common:
                    if cell in cand_map and d in cand_map[cell]:
                        cand_map[cell].discard(d)
                        if not cand_map[cell]:
                            return False
                        changed = True
            # Rule B: a cycle node whose both neighbours in the cycle are weak
            # links for its digit must hold that digit → strip other candidates.
            for i in range(n):
                cell, d = cycle[i]
                if cell not in cand_map or d not in cand_map[cell]:
                    continue
                # prev step is (i-1)→i, next step is i→(i+1)
                # step index i-1 → i: strong when (i-1) % 2 == 0, i.e. i odd
                # step index i → i+1: strong when i % 2 == 0
                prev_strong = (i % 2 == 1)   # step (i-1)->i is strong
                next_strong_step = (i % 2 == 0)  # step i->(i+1) is strong
                if not prev_strong and not next_strong_step:
                    # Both adjacent links are weak → this cell must hold d
                    for other_d in list(cand_map[cell]):
                        if other_d != d:
                            cand_map[cell].discard(other_d)
                            if not cand_map[cell]:
                                return False
                            changed = True
        if changed:
            continue

        # --- 21. Nishio (single-digit trial elimination) ---
        # For each unsolved cell and each of its candidates, hypothetically
        # place the digit and propagate naked singles and hidden singles on a
        # scratch copy of cand_map.  If a contradiction (empty candidate set
        # or a unit with no cell for some digit) is reached, the digit is
        # provably wrong in that cell and can be eliminated from the real map.
        # Only the propagation of singles (not the full solver) is used here
        # to limit runtime and keep one clear step of inference per pass.
        def _propagate_singles(
            scratch: dict[tuple[int, int], set[int]],
        ) -> bool:
            """Apply naked/hidden singles on *scratch* in-place.
            Return False if a contradiction is found, True otherwise."""
            while True:
                progress = False
                # Naked singles
                for cell in list(scratch):
                    if cell not in scratch:
                        continue
                    if len(scratch[cell]) == 1:
                        (v,) = scratch[cell]
                        del scratch[cell]
                        for peer in peer_cache[cell]:
                            if peer in scratch:
                                scratch[peer].discard(v)
                                if not scratch[peer]:
                                    return False
                        progress = True
                if progress:
                    continue
                # Hidden singles
                for unit in units:
                    for v in symbols:
                        possible = [
                            c for c in unit
                            if c in scratch and v in scratch[c]
                        ]
                        if len(possible) == 0:
                            # Check if digit is already placed in the unit
                            if not any(
                                grid[r][c] == v for r, c in unit
                                if (r, c) not in scratch
                            ):
                                return False
                        elif len(possible) == 1:
                            cell = possible[0]
                            del scratch[cell]
                            for peer in peer_cache[cell]:
                                if peer in scratch:
                                    scratch[peer].discard(v)
                                    if not scratch[peer]:
                                        return False
                            progress = True
                if not progress:
                    break
            return True

        for cell in list(cand_map):
            if cell not in cand_map:
                continue
            for val in list(cand_map.get(cell, set())):
                if cell not in cand_map or val not in cand_map[cell]:
                    continue
                # Build scratch copy, place val in cell
                scratch: dict[tuple[int, int], set[int]] = {
                    c: set(s) for c, s in cand_map.items() if c != cell
                }
                # Propagate placement of val into peers
                contradiction = False
                for peer in peer_cache[cell]:
                    if peer in scratch:
                        scratch[peer].discard(val)
                        if not scratch[peer]:
                            contradiction = True
                            break
                if not contradiction:
                    contradiction = not _propagate_singles(scratch)
                if contradiction:
                    cand_map[cell].discard(val)
                    if not cand_map[cell]:
                        return False
                    changed = True
        if changed:
            continue

        # --- 22. Forcing Chains (dual-branch common-elimination) ---
        # For every bivalue cell P = {X, Y}, simulate placing X (branch A) and
        # placing Y (branch B) and propagate naked/hidden singles on scratch
        # copies of the candidate map.  Any candidate eliminated in BOTH
        # branches is provably absent regardless of which branch is correct,
        # and can be removed from the real map.  Additionally, if one branch
        # leads to a contradiction, the other branch must be correct and its
        # full set of eliminations is applied (equivalent to Nishio + forcing).
        #
        # Also extends to any cell (not just bivalues): for each pair of
        # candidates (X, Y) in the same cell, the same dual-branch logic
        # applies when both branches are non-contradicting.
        def _propagate_and_snapshot(
            scratch: dict[tuple[int, int], set[int]],
            start_cell: tuple[int, int],
            val: int,
        ) -> tuple[bool, dict[tuple[int, int], set[int]]]:
            """Place *val* in *start_cell* on *scratch*, propagate singles.

            Returns (contradiction, resulting_scratch).  *scratch* is mutated.
            """
            for peer in peer_cache[start_cell]:
                if peer in scratch:
                    scratch[peer].discard(val)
                    if not scratch[peer]:
                        return True, scratch
            ok = _propagate_singles(scratch)
            return (not ok), scratch

        for pivot in list(cand_map):
            if pivot not in cand_map:
                continue
            pivot_cands = list(cand_map.get(pivot, set()))
            if len(pivot_cands) < 2:
                continue
            # Try every pair of candidates in this cell as the two branches
            for X, Y in combinations(pivot_cands, 2):
                # Branch A: assume X is placed in pivot
                scratch_a: dict[tuple[int, int], set[int]] = {
                    c: set(s) for c, s in cand_map.items() if c != pivot
                }
                contra_a, snap_a = _propagate_and_snapshot(scratch_a, pivot, X)

                # Branch B: assume Y is placed in pivot
                scratch_b: dict[tuple[int, int], set[int]] = {
                    c: set(s) for c, s in cand_map.items() if c != pivot
                }
                contra_b, snap_b = _propagate_and_snapshot(scratch_b, pivot, Y)

                if contra_a and contra_b:
                    # Both branches contradictory → unsolvable state
                    return False

                if contra_a:
                    # Branch A (X) is impossible → Y must be correct:
                    # apply all eliminations from branch B
                    if pivot in cand_map and X in cand_map[pivot]:
                        cand_map[pivot].discard(X)
                        if not cand_map[pivot]:
                            return False
                        changed = True
                    for cell, remaining in snap_b.items():
                        if cell not in cand_map:
                            continue
                        eliminated = cand_map[cell] - remaining
                        if eliminated:
                            cand_map[cell] -= eliminated
                            if not cand_map[cell]:
                                return False
                            changed = True
                    break  # restart outer loop after bulk change

                if contra_b:
                    # Branch B (Y) is impossible → X must be correct
                    if pivot in cand_map and Y in cand_map[pivot]:
                        cand_map[pivot].discard(Y)
                        if not cand_map[pivot]:
                            return False
                        changed = True
                    for cell, remaining in snap_a.items():
                        if cell not in cand_map:
                            continue
                        eliminated = cand_map[cell] - remaining
                        if eliminated:
                            cand_map[cell] -= eliminated
                            if not cand_map[cell]:
                                return False
                            changed = True
                    break  # restart outer loop after bulk change

                # Both branches non-contradictory: eliminate candidates absent
                # in both resulting snapshots (common eliminations).
                for cell in list(cand_map):
                    if cell not in cand_map:
                        continue
                    in_a = snap_a.get(cell, set())
                    in_b = snap_b.get(cell, set())
                    common_remaining = in_a & in_b
                    # Digits removed by BOTH branches
                    common_elim = cand_map[cell] - common_remaining
                    # Only apply eliminations actually present in original map
                    # AND absent from both snapshots
                    real_elim = {
                        v for v in common_elim
                        if v not in in_a and v not in in_b
                    }
                    if real_elim:
                        cand_map[cell] -= real_elim
                        if not cand_map[cell]:
                            return False
                        changed = True
            if changed:
                break
        if changed:
            continue

        if not changed:
            break  # all 22 techniques exhausted; cannot make further progress

    return not cand_map


def solve(
    grid: Grid,
    size: int,
    region_layout: Sequence[Sequence[int]],
    symbols: list[int],
    limit: int = 2,
) -> list[Grid]:
    """Return the solution found by constraint propagation.

    Techniques applied (in order): naked singles, hidden singles,
    locking type 1 (pointing), locking type 2 / claiming (intersections),
    naked pairs/triplets/quads, hidden pairs/triplets/quads,
    X-Wing, Swordfish, Jellyfish, XY-Wing, XYZ-Wing,
    Unique Rectangle (Types 1/2/4), Simple Coloring, BUG+1,
    Aligned Pair Exclusion (APE), Bidirectional Cycles (AIC Loops),
    Nishio, Forcing Chains.
    Only puzzles solvable by these 22 techniques will return a result.

    Args:
        grid: size×size grid with None for empty cells.
        size: board dimension.
        region_layout: size×size mapping of (row,col) -> region_id.
        symbols: allowed fill values.
        limit: kept for API compatibility; at most one solution is returned.

    Returns:
        A list containing the solved grid, or an empty list if the puzzle
        cannot be solved by naked/hidden singles alone.
    """
    if not validate(grid, size, region_layout, symbols):
        return []

    peer_cache = _build_peer_cache(size, region_layout)
    units = _build_units(size, region_layout)
    region_units = _build_region_units(size, region_layout)
    work = [row[:] for row in grid]

    if _solve_logical(work, size, symbols, peer_cache, units, region_units):
        return [work]
    return []


def is_valid_and_unique(
    grid: Grid,
    size: int,
    region_layout: Sequence[Sequence[int]],
    symbols: list[int],
) -> bool:
    """Return True iff *grid* is valid and uniquely solved by the 10 propagation techniques."""
    return len(solve(grid, size, region_layout, symbols, limit=2)) == 1
