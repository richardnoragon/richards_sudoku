# Kakuro

## Alpha alignment

Kakuro is in the current [Alpha scope](alpha.md). Record generation, run validation,
play, completion, and save/resume evidence; the format and generator descriptions
below do not certify Alpha readiness.

## Rules and implementation

The current New Game dialog generates 9×9 Kakuro boards. White cells contain digits
1–9; each across/down run must sum to its clue without repeated digits. There is
no global row, column, or box uniqueness. Black cells carry clues and are not editable.
Runs have at least two cells.

`KakuroTemplateLibrary` generates layouts procedurally from seeds and difficulty;
it does not select from an on-disk template pool. `KakuroFillGenerator` fills layouts,
and `KakuroWorker` manages background generation and retry/cancellation.
Candidate and grading logic use run constraints; `_KakuroRun` adds sum restrictions.
The controller checks filled runs, sums, and uniqueness at completion.

## Metadata and persistence

`variant_meta.constraints` contains:

- `black_cells`: zero-based `[row, column]` pairs.
- `clues`: run dictionaries with `cells`, `sum`, and `dir` (`across` or `down`).
- `clue_positions`: derived runtime lookup for rendering; omitted from saves and
  rebuilt by the loader.

Example run fragment, not a complete save:

```json
{"cells": [[1, 1], [1, 2]], "sum": 6, "dir": "across"}
```

See [MIGRATIONS.md](MIGRATIONS.md) for the full session format.
Tests live in `tests/test_kakuro.py`, `tests/test_persistence.py`, and `tests/test_text_format.py`.

## Rendering and input

Black clue cells have a diagonal split: down clue top-left, across clue bottom-right.
Selecting a white cell highlights its run peers. Arrow/Tab navigation skips black cells.
The current UI and remaining shared gaps are documented in [PROJECT_STATUS.md](PROJECT_STATUS.md).

## Text API

Common headers include `variant: kakuro`, `size: 9`, `seed`, and `difficulty`.
The mask header is `mask:` with nine `.`/`B` rows joined by `/`. Each run has its own
`clue:` header; coordinates are space-separated pairs. Example header fragment:

```text
clue: 1,1 1,2:6:across
```

Board rows are compact: `_` for black cells, `0` for empty white cells, and digits
for filled white cells. A complete file needs the full mask, run list, and board.
Import/Export menu actions support this text format and JSON sessions. The worker
uses run-aware bounded uniqueness checks and may retain extra given digits.
