"""Candidate computation service for Sudoku cells."""
from __future__ import annotations

from richards_sudoku.model.types import Board, VariantMetadata
from richards_sudoku.solver.solver import _build_peer_cache, _candidates

# Variant name strings used as anticipatory guards for Extended Variants
_KENKEN_VARIANT = "kenken"
_KAKURO_VARIANT = "kakuro"


def compute_candidates(
    board: Board,
    row: int,
    col: int,
    variant_meta: VariantMetadata,
) -> set[int]:
    """Return the set of valid candidates for a single empty cell.

    Returns an empty set if the cell already has a value or is black.
    """
    cell = board.cell(row, col)
    if cell.is_black or cell.value is not None:
        return set()

    grid = [[board.cell(r, c).value for c in range(board.size)] for r in range(board.size)]
    peer_cache = _build_peer_cache(
        board.size, variant_meta.region_layout,
        has_box_regions=variant_meta.constraints.get("has_box_regions", True),
    )
    return _candidates(grid, row, col, set(variant_meta.symbols), peer_cache)


def update_all_candidates(board: Board, variant_meta: VariantMetadata) -> None:
    """Recompute and store candidates for every empty, non-fixed cell in-place."""
    constraints = variant_meta.constraints

    # --- Kakuro early-exit branch (R15 Q3, Option A) ---
    # Kakuro has no global row/col uniqueness; peer elimination is wrong.
    # Only the run-sum/no-repeat filter applies.
    if variant_meta.name.value == _KAKURO_VARIANT:
        clues: list[dict] = constraints.get("clues", []) or []
        symbols = set(variant_meta.symbols)
        for r in range(board.size):
            for c in range(board.size):
                cell = board.cell(r, c)
                if cell.is_black:
                    cell.candidates = set()
                    continue
                if cell.value is None and not cell.is_fixed:
                    cell.candidates = _filter_kakuro_candidates(board, r, c, set(symbols), clues)
                elif cell.value is not None:
                    cell.candidates = set()
        return

    grid = [[board.cell(r, c).value for c in range(board.size)] for r in range(board.size)]
    peer_cache = _build_peer_cache(
        board.size, variant_meta.region_layout,
        has_box_regions=variant_meta.constraints.get("has_box_regions", True),
    )
    symbols = set(variant_meta.symbols)

    # Variant-specific setup
    black_set: set[tuple[int, int]] = set()
    if constraints.get("black_cells"):
        black_set = {(int(p[0]), int(p[1])) for p in constraints["black_cells"]}

    cages: list[dict] = constraints.get("cages", []) or []
    is_kenken = variant_meta.name.value == _KENKEN_VARIANT

    for r in range(board.size):
        for c in range(board.size):
            cell = board.cell(r, c)
            # Black cells (Str8ts / Kakuro) have no candidates
            if cell.is_black:
                cell.candidates = set()
                continue
            if cell.value is None and not cell.is_fixed:
                cands = _candidates(grid, r, c, symbols, peer_cache)

                # --- Str8ts straight filter ---
                if black_set:
                    cands = _filter_str8ts_candidates(board, r, c, cands, black_set)

                # --- Killer sum-feasibility filter ---
                if cages and not is_kenken:
                    cands = _filter_killer_candidates(board, r, c, cands, cages, symbols)

                # --- KenKen cage arithmetic feasibility filter ---
                if cages and is_kenken:
                    cands = _filter_kenken_candidates(board, r, c, cands, cages, symbols)

                cell.candidates = cands
            elif cell.value is not None:
                cell.candidates = set()


def _filter_str8ts_candidates(
    board: Board,
    row: int,
    col: int,
    cands: set[int],
    black_set: set[tuple[int, int]],
) -> set[int]:
    """Remove candidates that cannot participate in a valid straight in this row/col."""
    from richards_sudoku.services.str8ts_utils import _can_extend_straight

    size = board.size
    valid: set[int] = set()
    for v in cands:
        ok_row = _can_fit_in_line(board, row, col, v, size, black_set, axis="row")
        ok_col = _can_fit_in_line(board, row, col, v, size, black_set, axis="col")
        if ok_row or ok_col:
            valid.add(v)
    return valid


def _can_fit_in_line(
    board: Board,
    row: int,
    col: int,
    v: int,
    size: int,
    black_set: set[tuple[int, int]],
    axis: str,
) -> bool:
    """Return True if digit *v* can fit in the run containing (row,col) in *axis*."""
    from richards_sudoku.services.str8ts_utils import _can_extend_straight

    # Collect the run cells in this axis that contain (row,col)
    run: list[tuple[int, int]] = []
    if axis == "row":
        coords = [(row, c) for c in range(size)]
    else:
        coords = [(r, col) for r in range(size)]

    in_run = False
    for pos in coords:
        if pos in black_set:
            if in_run:
                break
        else:
            if axis == "row":
                if pos[1] == col:
                    in_run = True
            else:
                if pos[0] == row:
                    in_run = True
            run.append(pos)
    # Reset and rebuild properly
    run = []
    segment: list[tuple[int, int]] = []
    target_run: list[tuple[int, int]] = []
    for pos in coords:
        if pos in black_set:
            if segment:
                if (row, col) in segment:
                    target_run = list(segment)
                segment = []
        else:
            segment.append(pos)
    if segment and (row, col) in segment:
        target_run = list(segment)

    if not target_run or len(target_run) < 2:
        return False

    # Collect placed values in this run (excluding (row, col))
    placed = [
        board.cell(r, c).value
        for r, c in target_run
        if (r, c) != (row, col) and board.cell(r, c).value is not None
    ]
    return _can_extend_straight(placed, len(target_run), v)


def _filter_killer_candidates(
    board: Board,
    row: int,
    col: int,
    cands: set[int],
    cages: list[dict],
    symbols: set[int],
) -> set[int]:
    """Remove candidates that are inconsistent with cage sum constraints."""
    # Find which cage (row, col) belongs to
    target_cage = None
    for cage in cages:
        cells = [(int(p[0]), int(p[1])) for p in cage.get("cells", [])]
        if (row, col) in cells:
            target_cage = cage
            break

    if target_cage is None:
        return cands

    cage_sum = target_cage["sum"]
    cage_cells_all = [(int(p[0]), int(p[1])) for p in target_cage["cells"]]

    # Collect already-placed values in this cage (excluding this cell)
    filled = [
        board.cell(r, c).value
        for r, c in cage_cells_all
        if (r, c) != (row, col) and board.cell(r, c).value is not None
    ]
    remaining_cells = len(cage_cells_all) - len(filled) - 1  # cells after this one to fill
    filled_sum = sum(filled)
    remaining_sum = cage_sum - filled_sum  # must be achieved by (this cell + remaining_cells more)

    valid: set[int] = set()
    for v in cands:
        need = remaining_sum - v  # sum needed from remaining_cells more cells
        if need < 0:
            continue
        if remaining_cells == 0:
            if need == 0:
                valid.add(v)
        else:
            # Check if need can be achieved by remaining_cells distinct digits
            # from symbols, excluding already filled and v
            used = set(filled) | {v}
            avail = [s for s in symbols if s not in used]
            if _can_sum_to(avail, remaining_cells, need):
                valid.add(v)
    return valid


def _can_sum_to(available: list[int], count: int, target: int) -> bool:
    """Return True if *count* distinct values from *available* sum to *target*."""
    if count == 0:
        return target == 0
    if count > len(available):
        return False
    from itertools import combinations
    for combo in combinations(available, count):
        if sum(combo) == target:
            return True
    return False


def _filter_kenken_candidates(
    board: Board,
    row: int,
    col: int,
    cands: set[int],
    cages: list[dict],
    symbols: set[int],
) -> set[int]:
    """Remove candidates that are inconsistent with KenKen cage arithmetic."""
    target_cage = None
    for cage in cages:
        cells = [(int(p[0]), int(p[1])) for p in cage.get("cells", [])]
        if (row, col) in cells:
            target_cage = cage
            break

    if target_cage is None:
        return cands

    op: str = target_cage.get("op", "+")
    target: int = int(target_cage.get("target", target_cage.get("sum", 0)))
    cage_cells_all = [(int(p[0]), int(p[1])) for p in target_cage["cells"]]
    n = len(cage_cells_all)

    # Collect already-placed values in this cage (excluding this cell)
    placed = [
        board.cell(r, c).value
        for r, c in cage_cells_all
        if (r, c) != (row, col) and board.cell(r, c).value is not None
    ]
    unfilled_count = n - len(placed) - 1  # remaining empty cells after (row,col)

    valid: set[int] = set()

    for v in cands:
        all_vals = placed + [v]

        if op == "+":
            # Partial sum must not exceed target; remaining cells must be able to reach target
            partial = sum(all_vals)
            if partial > target:
                continue
            need = target - partial
            used = set(all_vals)
            avail = [s for s in symbols if s not in used]
            if unfilled_count == 0:
                if need == 0:
                    valid.add(v)
            else:
                if _can_sum_to(avail, unfilled_count, need):
                    valid.add(v)

        elif op == "×" or op == "*":
            # Partial product must divide target evenly
            partial = 1
            for x in all_vals:
                partial *= x
            if target % partial != 0:
                continue
            remaining_product = target // partial
            if unfilled_count == 0:
                if remaining_product == 1:
                    valid.add(v)
            else:
                # Check if remaining cells can produce remaining_product
                used = set(all_vals)
                avail = [s for s in symbols if s not in used]
                if _can_product_to(avail, unfilled_count, remaining_product):
                    valid.add(v)

        elif op == "-" or op == "−":
            # Two-cell cage only: |a - b| = target
            if n == 1:
                if v == target:
                    valid.add(v)
            elif n == 2:
                other_vals = [x for x in placed if x is not None]
                if not other_vals:
                    # Other cell not yet placed — check if any valid partner exists
                    for s in symbols:
                        if s != v and abs(v - s) == target:
                            valid.add(v)
                            break
                else:
                    if abs(v - other_vals[0]) == target:
                        valid.add(v)
            else:
                # Subtraction cages > 2 cells: allow (spec leaves undefined, pass through)
                valid.add(v)

        elif op == "÷" or op == "/":
            # Two-cell cage only: max/min = target
            if n == 1:
                if v == target:
                    valid.add(v)
            elif n == 2:
                other_vals = [x for x in placed if x is not None]
                if not other_vals:
                    for s in symbols:
                        if s != v and (
                            (v != 0 and s % v == 0 and s // v == target) or
                            (s != 0 and v % s == 0 and v // s == target)
                        ):
                            valid.add(v)
                            break
                else:
                    a, b = v, other_vals[0]
                    if a != 0 and b != 0:
                        if (max(a, b) // min(a, b) == target and max(a, b) % min(a, b) == 0):
                            valid.add(v)
            else:
                valid.add(v)

        else:
            # Unknown operation — pass through
            valid.add(v)

    return valid if valid else cands


def _can_product_to(available: list[int], count: int, target: int) -> bool:
    """Return True if *count* distinct values from *available* multiply to *target*."""
    if count == 0:
        return target == 1
    if count > len(available):
        return False
    from itertools import combinations
    for combo in combinations(available, count):
        p = 1
        for x in combo:
            p *= x
        if p == target:
            return True
    return False


def _filter_kakuro_candidates(
    board: Board,
    row: int,
    col: int,
    cands: set[int],
    clues: list[dict],
) -> set[int]:
    """Remove candidates inconsistent with Kakuro run-sum and no-repeat constraints.

    For each run (across / down) that contains (row, col):
    - Exclude digits already placed elsewhere in the run (no-repeat).
    - Exclude digits that make partial sum exceed target.
    - Exclude digits where remaining empty cells cannot possibly reach target sum.
    """
    valid = set(cands)

    for clue in clues:
        cells = [(int(p[0]), int(p[1])) for p in clue.get("cells", [])]
        if (row, col) not in cells:
            continue

        target_sum: int = int(clue["sum"])
        n = len(cells)

        placed_in_run = [
            board.cell(r, c).value
            for r, c in cells
            if (r, c) != (row, col) and board.cell(r, c).value is not None
        ]
        placed_set = set(placed_in_run)
        partial_sum = sum(placed_in_run)
        unfilled = n - len(placed_in_run) - 1  # cells still empty after (row,col)

        remove: set[int] = set()
        for v in list(valid):
            # No repeats within a run
            if v in placed_set:
                remove.add(v)
                continue
            # Partial sum ceiling
            new_partial = partial_sum + v
            if new_partial > target_sum:
                remove.add(v)
                continue
            # Feasibility: remaining cells must be able to complete the sum
            need = target_sum - new_partial
            if unfilled == 0:
                if need != 0:
                    remove.add(v)
            else:
                used = placed_set | {v}
                avail = [s for s in range(1, 10) if s not in used]
                if not _can_sum_to(avail, unfilled, need):
                    remove.add(v)

        valid -= remove

    return valid if valid else cands

