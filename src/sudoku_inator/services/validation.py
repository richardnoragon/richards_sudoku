"""Shared partial-board checks for painting, Check Board, and completion."""
from math import prod

from sudoku_inator.model.types import Board, Variant, VariantMetadata


def conflict_cells(board: Board, meta: VariantMetadata) -> set[tuple[int, int]]:
    size = board.size
    variant = meta.name
    constraints = meta.constraints
    conflicts = set()
    units = []
    if variant != Variant.KAKURO:
        units.extend([[(r, c) for c in range(size)] for r in range(size)])
        units.extend([[(r, c) for r in range(size)] for c in range(size)])
    if variant not in (Variant.KAKURO, Variant.KENKEN, Variant.STR8TS) and constraints.get("has_box_regions", True):
        regions = {}
        for r in range(size):
            for c in range(size):
                regions.setdefault(meta.region_layout[r][c], []).append((r, c))
        units.extend(regions.values())
    if variant == Variant.KAKURO:
        units.extend([list(map(tuple, run["cells"])) for run in constraints.get("clues", [])])
    if variant == Variant.KILLER:
        units.extend([list(map(tuple, cage["cells"])) for cage in constraints.get("cages", [])])
    for unit in units:
        seen = {}
        for r, c in unit:
            value = board.cell(r, c).value
            if value is not None:
                seen.setdefault(value, []).append((r, c))
        for cells in seen.values():
            if len(cells) > 1:
                conflicts.update(cells)
    for r in range(size):
        for c in range(size):
            value = board.cell(r, c).value
            if value is not None and value not in meta.symbols:
                conflicts.add((r, c))
    if variant == Variant.STR8TS:
        for line in [[(r, c) for c in range(size)] for r in range(size)] + [
            [(r, c) for r in range(size)] for c in range(size)
        ]:
            runs = [[]]
            for r, c in line:
                if board.cell(r, c).is_black:
                    runs.append([])
                else:
                    runs[-1].append((r, c))
            for run in runs:
                values = [board.cell(r, c).value for r, c in run if board.cell(r, c).value is not None]
                if values and max(values) - min(values) >= len(run):
                    conflicts.update(run)
    groups = constraints.get("clues", []) if variant == Variant.KAKURO else constraints.get("cages", [])
    for group in groups:
        cells = [tuple(p) for p in group["cells"]]
        values = [board.cell(r, c).value for r, c in cells if board.cell(r, c).value is not None]
        remaining = len(cells) - len(values)
        target = group.get("sum", group.get("target"))
        op = group.get("op", "+")
        bad = False
        if op == "+":
            total = sum(values)
            bad = total + remaining * min(meta.symbols) > target or total + remaining * max(meta.symbols) < target
        elif op == "*":
            product = prod(values)
            bad = product > target or target % product != 0 or (remaining == 0 and product != target)
        elif remaining == 0 and values:
            if op == "-":
                bad = max(values) - min(values) != target
            elif op == "/":
                bad = max(values) != min(values) * target
        if bad:
            conflicts.update(cells)
    return conflicts
