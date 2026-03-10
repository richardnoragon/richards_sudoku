"""Debug script for Str8ts filter issue."""
from richards_sudoku.model.types import Board, Variant, VariantMetadata
from richards_sudoku.services.candidates import update_all_candidates
from richards_sudoku.services.str8ts_utils import _can_extend_straight

def _str8ts_meta_with_black(black_cells):
    meta = VariantMetadata.standard_9x9()
    return VariantMetadata(
        name=Variant.STR8TS, size=9, symbols=list(range(1, 10)),
        region_layout=meta.region_layout,
        constraints={'black_cells': list(black_cells)},
    )

black_cells = [(0, c) for c in range(2, 9)] + [(r, 1) for r in range(2, 9)]
meta = _str8ts_meta_with_black(black_cells)
board = Board(size=9, variant=Variant.STR8TS)
for pos in black_cells:
    board.cell(*pos).is_black = True
board.cell(0, 0).value = 1
board.cell(1, 1).value = 1
update_all_candidates(board, meta)
cands = board.cell(0, 1).candidates
print('cands:', sorted(cands))
print('9 in cands:', 9 in cands)
print()

# Direct _can_extend_straight test
r1 = _can_extend_straight([1], 2, 9)
print('_can_extend_straight([1], 2, 9):', r1)

# Build black_set manually
black_set = {(int(p[0]), int(p[1])) for p in meta.constraints['black_cells']}
print('black_set sample:', sorted(black_set)[:5], '...len=', len(black_set))
print('(0,2) in black_set:', (0,2) in black_set)
print('(2,1) in black_set:', (2,1) in black_set)
print('(1,1) in black_set:', (1,1) in black_set)

# Manually run _can_fit_in_line for (0,1) row
size = 9
row, col = 0, 1
axis = "row"
coords = [(row, c) for c in range(size)]
segment = []
target_run = []
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
print('ROW target_run:', target_run)

# COL direction
axis = "col"
coords2 = [(r, col) for r in range(size)]
segment2 = []
target_run2 = []
for pos in coords2:
    if pos in black_set:
        if segment2:
            if (row, col) in segment2:
                target_run2 = list(segment2)
            segment2 = []
    else:
        segment2.append(pos)
if segment2 and (row, col) in segment2:
    target_run2 = list(segment2)
print('COL target_run:', target_run2)
