# Kakuro — Design Notes

## Core Concept

Kakuro is often called "Cross-Sums" — it combines a crossword grid layout with digit
arithmetic. The puzzle grid contains **black cells** (walls and clue headers) and **white
cells** (fillable). Every maximal run of consecutive white cells in the same row or column
must sum to the adjacent clue number and must not repeat any digit 1–9.

Unlike Sudoku there is **no global row/column uniqueness** — the same digit may appear in
different runs within the same row or column.

---

## Rules

- White cells are filled with digits 1–9.
- Each **run** (maximal consecutive white cells in one row or column):
  - Must sum exactly to the clue number given in the adjacent black-cell header.
  - Must contain distinct digits (no repeated digit within a single run).
  - Minimum run length is 2 (single-white-cell runs are disallowed by design).
- Black cells cannot be edited; they carry the clue numbers.
- No global row/column or box uniqueness constraint — only per-run constraints apply.

---

## Grid Structure

- Bounding box: N×N for typical N ∈ {9, 12, 16}.
- Black cells: wall + optionally one or two clue numbers (across and/or down).
- White cells: fillable 1–9.
- Clue position convention (standard Kakuro):
  - **Down clue** in the top-left area of the black cell.
  - **Across clue** in the bottom-right area of the black cell.
  - Separated by a diagonal line rendered in `Palette.cage_label_color`.

---

## Generator Strategy

```python
# Pseudocode
template = KakuroTemplateLibrary.select(seed % len(library))
filler   = KakuroFillGenerator(template, seed, rng)
solution = filler.fill()          # backtracking, sum + no-repeat pruning
# Expose clue numbers; no white-cell digits pre-filled
# Verify unique solution before returning meta
```

**`KakuroTemplateLibrary`** (`solver/variant_generators.py`):
- Stores a small curated pool of grid templates (black/white cell layouts + run topology).
- `seed % pool_size` selects the template class; per-template seed drives fill order.
- Each template guarantees minimum run length ≥ 2 and full white-cell coverage.

**`KakuroFillGenerator`**:
- Backtracking fill respecting sum feasibility and no-repeat-per-run at each placement.
- Pruning: if `partial_run_sum + v > target` or not enough distinct digits remain to
  reach `target − partial_sum`, that candidate is skipped.
- Accepts optional `cancel_flag`.

`KakuroWorker` runs generation on a background thread (same `moveToThread` + cancel pattern),
populating:
- `meta.constraints["clues"]`           — run list with sums and directions.
- `meta.constraints["black_cells"]`     — black-cell positions (reuses Str8ts field).
- `meta.constraints["clue_positions"]`  — per-cell across/down clue values.

---

## Solving & SE Grader

All row/column/region techniques from Standard do **not** apply here (different constraint
model). The Kakuro-specific technique is:

**`_KakuroRun` (weight 2.1)** — added to `_TECHNIQUES` after `_KenKenCage`:

- For each run, restricts per-cell candidates using:
  1. Run-sum feasibility: exclude `v` if `partial_sum + v > target` or
     `remaining_cells × max_unused_distinct < target − partial_sum`.
  2. Already-placed digits in the same run: exclude any digit already used in the run.
- Analogous in structure to `_Str8tsRun` (run-based elimination) but uses sum arithmetic.
- No permutation cap needed for typical run lengths ≤ 9.
- Fires only when `meta.name == Variant.KAKURO`.

*Note*: Standard techniques (_HiddenSingle, _NakedPair, etc.) still apply at the per-run
candidate level since each run is effectively a "unit" in the Kakuro constraint model.
`_build_unit_groups` for Kakuro returns one unit per run (across and down), replacing the
usual row/col/box units.

---

## Persistence

```json
{
  "variant": "kakuro",
  "size": 9,
  "constraints": {
    "black_cells": [[0,0],[0,3],[1,2]],
    "clue_positions": [
      {"row": 0, "col": 0, "across": null, "down": 15},
      {"row": 0, "col": 3, "across": 6,    "down": null}
    ],
    "clues": [
      {"run_cells": [[0,1],[0,2]], "sum": 6,  "dir": "across"},
      {"run_cells": [[1,0],[2,0]], "sum": 15, "dir": "down"}
    ]
  }
}
```

- `black_cells` reuses the Str8ts field name (consistency).
- No schema version bump required.

---

## UI Notes

### Black Cell Rendering
- Black cells render with `Palette.black_cell_bg` (reuses Str8ts colour).
- Clue-bearing black cells additionally render:
  - A **diagonal dividing line** (top-left to bottom-right) in `Palette.cage_label_color`.
  - **Down clue** number in the top-left half (small font).
  - **Across clue** number in the bottom-right half (small font).
  - If only one direction is present, only that half is labelled.
- This is a new rendering branch in `_draw_board`, keyed on whether the cell's position
  appears in `meta.constraints["clue_positions"]`.

### Run Peer Highlight
- Selecting any white Kakuro cell highlights all cells in its across-run **and** down-run
  with `Palette.peer_bg` tint (both runs together).
- Derived at render time from `meta.constraints["clues"]` — no extra index needed.

### Navigation
- Arrow keys and Tab skip black cells using the existing `_move_selection` /
  `_advance_selection` skip-black logic (the same logic introduced for Str8ts).

### Conflict Highlighting
- Flags cells in a run whose partial-sum state exceeds the clue target.
- Flags cells that cannot reach the clue target given remaining empty cells and
  available distinct candidates.
- Flags duplicate digits within the same run.

---

## `is_complete` Check

```python
# Inside GameController.is_complete (inline, same pattern as Killer/KenKen)
if self._meta.name == Variant.KAKURO:
    for clue in self._meta.constraints["clues"]:
        vals = [self._board.cell(r, c).value for r, c in clue["run_cells"]]
        if not all(vals):
            return False
        if sum(vals) != clue["sum"]:
            return False
        if len(set(vals)) != len(vals):   # intra-run duplicate check
            return False
```

---

## Import / Export (Text Format)

```
variant: kakuro
size: 9
seed: 42
difficulty: hard
black_cells: B....BB../....B..../B....BB..
clues:
1,1,1,2:6:across
1,0,2,0:15:down
...

_ 0 0 _ 0 0 0 _ _
...
```

- `black_cells` encoded as `.`/`B` per row joined by `/` (same as Str8ts mask format).
- Each clue line: comma-separated `row,col` pairs, then `:sum:dir`.
- Digit rows use `0` for empty whites and `_` for black cells.

---

## Harmonisation Notes

| Integration point     | Approach                                                        |
|-----------------------|-----------------------------------------------------------------|
| `Variant` enum        | `KAKURO = "kakuro"` added in Batch J                            |
| `Cell.is_black`       | Reused directly; Kakuro black cells behave like Str8ts black    |
| Variant registry      | Factory registered; `_KakuroRun` constraint callback            |
| Background worker     | `KakuroWorker` — same moveToThread + cancel                     |
| `_draw_edges`         | Extended: diagonal clue labels in black-cell rendering branch   |
| Unit groups           | One unit per run (across and down) replaces rows/cols/boxes     |
| SE grader             | `_KakuroRun` (2.1) + standard techniques on run units           |
| Persistence           | `constraints["black_cells"]`, `["clues"]`, `["clue_positions"]`|
| `is_complete`         | Inline run-sum + intra-run uniqueness check                     |
| Navigation            | Skip-black logic reused from Str8ts                             |
| Conflict detection    | Run-sum excess/deficit + per-run digit duplicate                |
