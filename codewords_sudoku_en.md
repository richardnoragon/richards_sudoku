# Codewords Sudoku

## Alpha alignment

Codewords is in the current [Alpha scope](alpha.md). DOC-05 has implementation and regression
evidence; independent handoff and manual acceptance remain in PROJECT_STATUS.md.

## Current implementation

9×9 Sudoku with letters A–I displayed in place of digits. The model, solver,
candidates, and completion checks operate on digits 1–9 using standard regions.
`CodewordsGenerator` creates a bijective codebook and a difficulty-dependent
`given_mappings` subset; `CodewordsWorker` runs the generation flow.

The shell displays only given mappings as locked fields. Other slots hold editable,
distinct digit hypotheses with undo/redo and JSON persistence in
`board.codebook_hypotheses`. These notes do not alter the solution mapping. Grid
entry uses digits; hidden mapping values remain in the save/text metadata.
`_CodewordsMapping` participates in the SE-style grader alongside the shared techniques.

## Metadata and persistence

`variant_meta.constraints` contains `codebook` (all A–I mapped to all digits 1–9)
and `given_mappings` (a consistent subset). Both are saved under schema version 2.
See [MIGRATIONS.md](MIGRATIONS.md) for the enclosing session structure.

## Text API

The text API requires a complete `codebook:` header; `given_mappings:` is optional
and omitted by the exporter when empty. Rows contain nine characters: A–I for values,
`0` for empty cells. This illustrative empty board has valid format, not a unique puzzle:

```text
variant: codewords
size: 9
seed: 42
difficulty: medium
codebook: A=1,B=2,C=3,D=4,E=5,F=6,G=7,H=8,I=9
given_mappings: A=1,C=3
000000000
000000000
000000000
000000000
000000000
000000000
000000000
000000000
000000000
```

Imports validate the bijection and consistency of given mappings. The codebook is
exported explicitly; it is not inferred from the grid. The UI supports text and JSON import/export; text omits player hypotheses.
Tests: `tests/test_codewords.py`, `tests/test_text_format.py`.
