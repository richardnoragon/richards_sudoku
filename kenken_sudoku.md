# KenKen (Calcudoku)

## Alpha alignment

KenKen is in the current [Alpha scope](alpha.md). Record end-to-end generation,
entry, completion, and save/resume evidence at each offered board size; model and
format support alone does not certify readiness.

## Rules and implementation

The New Game dialog offers 4×4, 6×6, and 9×9 boards. Digits 1–N are unique within
each row and column; there are no box regions (`has_box_regions = False`). Cages
have a target and an arithmetic operator: sum, product, difference, or quotient.
Subtraction and division use two-cell cages. A single-cell cage fixes its target value.

`KenKenCagePartitioner` produces cages; `KenKenWorker` performs background generation.
The partitioner creates its own seeded RNG. Candidate filtering, solver checks,
`_KenKenCage` grading, rendering, and controller completion checks have variant paths.
See `tests/test_kenken.py` for implemented scenarios and
[PROJECT_STATUS.md](PROJECT_STATUS.md) for shared UI limitations.

## Metadata and persistence

`variant_meta.constraints` contains `has_box_regions: false` and `cages`.
Each cage has `cells` (zero-based row/column pairs), `op`, and integer `target`.
Supported serialized operators are `+`, `-`, `*`, `/`. Single-cell cages use `+`;
an empty operator is not accepted by the JSON loader.

Example cage fragment, not a complete save:

```json
{"cells": [[0, 0], [0, 1]], "op": "+", "target": 5}
```

Load validation checks operators and non-overlapping full-board cage coverage.
The session format is documented in [MIGRATIONS.md](MIGRATIONS.md).

## Text API

Use common `variant: kenken`, `size`, `seed`, and `difficulty` headers. Add one
`cage:` header per cage. Coordinates are space-separated pairs:

```text
cage: 0,0 0,1:+:5
cage: 0,2:+:3
```

These are header fragments; a complete puzzle requires all cages and N board rows.
The exporter emits compact digit rows (`0` for empty cells). The menu integration
is implemented for text/JSON; `services/text_format.py` remains the programmatic API.
Generation retains enough clues to prove uniqueness within a bounded search.
