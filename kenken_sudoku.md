# KenKen (Calcudoku) — Design Notes

## Core Concept

KenKen (also called Calcudoku) is an N×N Latin-square puzzle. Unlike Sudoku it has **no
3×3 box uniqueness constraint** — only rows and columns must contain each digit exactly once.
The grid is divided into non-overlapping **cages**, each carrying an arithmetic operation
(+, −, ×, ÷) and a target value. Players must fill the grid so that the Latin-square rule
is satisfied and every cage's arithmetic is correct.

---

## Rules

- Grid is N×N for N ∈ {4, 6, 9}. Default new-game size: 9.
- Each digit 1–N appears exactly once per **row** and exactly once per **column**.
- No box-region uniqueness (KenKen is a Latin square, not a Sudoku).
- Every cage has a **target** and one **operation**:
  - `+`  — cell values sum to target (cage size ≥ 1).
  - `×`  — cell values multiply to target (cage size ≥ 1).
  - `−`  — exactly 2 cells; `|v₁ − v₂| = target` (order irrelevant).
  - `÷`  — exactly 2 cells; `max / min = target` (must divide exactly).
  - *(no op)* — single-cell cage; value equals target (acts as a given clue).
- A cage may not repeat a digit (in addition to the Latin-square rule).

---

## Grid Structure

- Size: N×N (N ∈ {4, 6, 9}).
- Regions: **none** (`has_box_regions = False`).
- `meta.region_layout` is unused; peer cache is built from rows/cols only.
- Cage boundaries replace box borders visually.

---

## Generator Strategy

```python
# Pseudocode
latin_square = fill_nxn_latin_square(n, rng)        # row+col only
partitioner = KenKenCagePartitioner(n, seed, rng)
cages = partitioner.partition(latin_square)          # assigns op + target
# Remove all digits; leave cage boundaries + labels
# Verify unique solution with cage-arithmetic callback
```

**`KenKenCagePartitioner`** (`solver/variant_generators.py`):
- Seeded flood-fill from the same `rng` instance used for the Latin-square fill.
- Difficulty-scaled cage-size distribution:
  - Easy: avg 2–3 cells (`-`/`÷` preferred for 2-cell cages)
  - Medium: avg 3–4 cells
  - Hard/Expert: avg 4–5 cells
- Operation assignment per cage:
  - 2-cell cage: try `÷` first (if values divide exactly), then `−`.
  - Multi-cell cage: try `×` first (if product ≤ n³ approx.), then `+`.
  - Single-cell cage: no operation; target = cell value; `is_fixed = True`.
- Returns `list[{"cells": [(r,c),...], "op": "+"|"-"|"*"|"/"|"", "target": int}]`.
- Accepts optional `cancel_flag`.

`KenKenWorker` runs generation on a background thread (same `moveToThread` + cancel pattern).

---

## Solving & SE Grader

**`_KenKenCage` (weight 1.9)** — added to `_TECHNIQUES` after `_KillerCage`:

- For each cage, applies operation-specific candidate restriction:
  - `+` / `×`: enumerate valid digit assignments (sum/product feasibility filter),
    analogous to `_KillerCage`; permutation cap 10 000.
  - `−`: for each candidate `v` in a 2-cell cage cell, verify there exists
    a valid value `w` in the paired cell such that `|v − w| = target`.
  - `÷`: for each candidate `v`, verify a valid `w` exists such that
    `max(v,w) / min(v,w) = target` is an exact integer.
- When the cap is reached, preserves current narrowed candidates (safe, same as Killer).
- Fires only when `meta.name == Variant.KENKEN`.

---

## Persistence

```json
{
  "variant": "kenken",
  "size": 9,
  "constraints": {
    "has_box_regions": false,
    "cages": [
      {"cells": [[0,0],[0,1]], "op": "-", "target": 3},
      {"cells": [[0,2]]      , "op": "" , "target": 7},
      {"cells": [[1,0],[2,0],[2,1]], "op": "+", "target": 12}
    ]
  }
}
```

- `"op": ""` encodes single-cell given cages.
- No schema version bump required.

---

## UI Notes

### Cage Rendering
- Reuses `_draw_edges` from Killer; cage boundaries drawn with the same thick pen.
- Cage label in the **topmost-leftmost cell** (row-major minimum):
  - Format: `"target op"` — e.g. `"12+"`, `"6×"`, `"2÷"`, `"3−"`.
  - Single-cell given: just the digit (bold, no operation).
  - Label at ~20–25% cell height; pencil-mark grid shifts down/right to avoid overlap
    (same as Killer, R6 Q7 pattern).

### Cage Member Highlight
- Selecting any KenKen cell subtly shades all other cells in the same cage with
  `Palette.cage_member_bg`.
- Priority chain: `selected > conflict > peer > cage_member > fixed > base`.

### Conflict Highlighting
- Flags row/column duplicates (standard Latin-square violations).
- Flags cage cells whose partial arithmetic is provably violated (partial sum/product
  exceeds or cannot reach target given remaining distinct candidates in the cage).

---

## `is_complete` Check

```python
# Inside GameController.is_complete (inline, same pattern as Killer)
if self._meta.name == Variant.KENKEN:
    for cage in self._meta.constraints["cages"]:
        vals = [self._board.cell(r, c).value for r, c in cage["cells"]]
        if not all(vals):
            return False
        op, target = cage["op"], cage["target"]
        if op == "+":  result = sum(vals)
        elif op == "*": result = math.prod(vals)
        elif op == "-": result = abs(vals[0] - vals[1])
        elif op == "/": result = max(vals) // min(vals)
        else:           result = vals[0]   # single-cell
        if result != target:
            return False
```

---

## Import / Export (Text Format)

```
variant: kenken
size: 9
seed: 42
difficulty: medium
cages:
0,0,0,1:+:12
0,2:*:6
1,0,1,1:-:3
...

0 0 0 0 0 0 0 0 0
...
```

- Each cage line: comma-separated `row,col` pairs, then `:op:target`.
- Empty op for single-cell givens.
- Digit rows are space-separated; `0` = empty.

---

## Harmonisation Notes

| Integration point     | Approach                                                   |
|-----------------------|------------------------------------------------------------|
| `Variant` enum        | `KENKEN = "kenken"` added in Batch J                       |
| Variant registry      | Factory registered; cage-arithmetic `constraint_ok` cb     |
| Background worker     | `KenKenWorker` — same moveToThread + cancel                |
| Peer cache            | Row + col only (`has_box_regions = False`)                 |
| `_draw_edges`         | Reused from Killer; cage boundaries with thick pen         |
| SE grader             | `_KenKenCage` (1.9) + all 17 standard techniques           |
| Persistence           | `constraints["cages"]` with `"op"` field                   |
| `is_complete`         | Inline cage-arithmetic check in `GameController`           |
| Conflict detection    | Row/col duplicates + cage-arithmetic violation             |
