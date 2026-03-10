# Codewords Sudoku — Design Notes

## Core Concept

Codewords Sudoku is a 9×9 variant where the digits 1–9 are replaced by the letters **A–I**.
A hidden bijective **codebook** maps each letter to exactly one digit and vice versa.
The puzzle reveals a difficulty-scaled subset of the codebook as clues alongside the standard
fixed-cell clues. Players must simultaneously solve the grid **and** deduce any unrevealed
letter-to-digit assignments.

Beneath the surface it is a standard Sudoku — row, column, and 3×3 box uniqueness all apply.
The letter layer is purely presentational; the model stores and solves at the digit layer.

---

## Rules

- The 9×9 grid obeys standard Sudoku uniqueness (rows, columns, 3×3 boxes).
- Every cell value corresponds to a letter A–I whose digit assignment is fixed globally for
  the entire puzzle (the codebook).
- A **given mapping** entry (e.g. `A = 3`) is revealed as a clue, locking that
  letter-to-digit assignment for the player.
- On Easy difficulty ≥ 5 given mappings are revealed; Expert may reveal 0.
- When 0 given mappings are shown, the player infers the full codebook from grid constraints alone.

---

## Grid Structure

- Size: 9×9 (same as Standard).
- Regions: standard 3×3 boxes (same as Standard).
- Cell display: letters A–I (rendered by `SudokuGridWidget`; stored internally as 1–9).
- Codebook Panel: a compact strip below the grid showing all 9 letter slots with their
  assigned or hypothesised digit values.

---

## Generator Strategy

```python
# Pseudocode
solution = standard_9x9_backtracking(seed)           # digits 1–9
mapping = random_bijection(letters="ABCDEFGHI",
                           digits=[1..9], seed=seed)  # letter -> digit
given_mappings = select_by_difficulty(mapping, difficulty)  # subset revealed
clue_cells = remove_digits(solution, _DIFFICULTY_GIVENS[difficulty])
# Verify unique solution under digit layer before returning
```

`CodewordsWorker` runs generation on a background thread, populating:
- `meta.constraints["codebook"]`       — full bijection (hidden from player)
- `meta.constraints["given_mappings"]` — revealed subset

---

## Solving & SE Grader

All 17 standard SE techniques apply at the digit layer (unchanged).

**`_CodewordsMapping` (weight 1.3)** — new technique added to `_TECHNIQUES` before
`_HiddenSingleBlock`:

- Iterates over unassigned letters (those absent from `given_mappings`).
- For each such letter, checks whether all cells bearing that letter in the grid have had
  their digit candidates reduced to a single value `d`.
- If so: the mapping `letter → d` is now forced; add it to the working `given_mappings`
  and eliminate digit `d` from the candidate sets of all other unassigned letters.
- Each firing of this technique counts as one SE step (weight 1.3).

---

## Persistence

```json
{
  "variant": "codewords",
  "constraints": {
    "codebook":       {"A": 3, "B": 7, "C": 1, ...},
    "given_mappings": {"A": 3, "C": 1}
  }
}
```

- `codebook`: written on save; used in `SudokuGridWidget` for display; not shown directly
  to the player.
- `given_mappings`: the subset the player sees/edits; restored on load.
- No schema version bump required.

---

## UI Notes

### Grid Display
- `SudokuGridWidget` calls `inverse_codebook[cell.value]` to obtain the display letter.
- Pencil marks are stored as digit candidate sets; rendered as letter candidates using
  the same `inverse_codebook` lookup.
- Confirmed entries render in the standard confirmed colour.
- Fixed (is_fixed) cells in letters are bold, same as Standard.

### Codebook Panel
- Compact horizontal widget (placed below or beside the grid).
- 9 slots labelled A–I, each with a digit input field.
- Given-mapping slots: bold, locked (rendered with `fixed_bg`).
- Player-hypothesis slots: editable, lighter style.
- Ctrl+Z / Ctrl+Y undo/redo applies to codebook edits too.
- Keyboard accessible (Tab navigates between slots).

---

## Import / Export (Text Format)

```
variant: codewords
size: 9
seed: 42
difficulty: medium
given_mappings: A=3,C=7
_____A_BC
A_______B
...
```

- Digit rows use letters (A–I); `_` for empty cells.
- `given_mappings` line lists only the revealed pairs.
- The hidden `codebook` is **not** exported in text format; import re-derives it from the
  grid on load (or stores it opaquely in JSON).

---

## Harmonisation Notes

| Integration point     | Approach                                             |
|-----------------------|------------------------------------------------------|
| `Variant` enum        | `CODEWORDS = "codewords"` added in Batch J           |
| Variant registry      | `CODEWORDS` factory registered; no constraint_ok cb  |
| Background worker     | `CodewordsWorker` — same moveToThread + cancel       |
| `_draw_edges`         | Standard — standard 3×3 box borders; no changes      |
| SE grader             | `_CodewordsMapping` (1.3) + all 17 standard techniques |
| Persistence           | `constraints["codebook"]` + `["given_mappings"]`     |
| `is_complete`         | Standard validation (digit layer) — no extra check   |
| Conflict detection    | Standard row/col/region at digit layer               |
