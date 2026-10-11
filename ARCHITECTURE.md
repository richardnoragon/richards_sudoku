# Architecture

## Alpha alignment

Alpha requires sufficiently stable module, configuration, and storage decisions.
The structure below is the current baseline; DOC-09 must record the independent
review and extension exercise required by [alpha.md](alpha.md).

Sudoku-inator is a layered Python/PyQt6 desktop application. The implementation
snapshot and known limitations are maintained in [PROJECT_STATUS.md](PROJECT_STATUS.md).

## Modules and ownership

| Module | Responsibility |
| --- | --- |
| `main.py` | `MainWindow`, menus, toolbar, status bar, codebook dock, controller wiring |
| `controller/game_controller.py` | Active board, solution, timer, stats, undo/redo, hints, completion, save/load |
| `model/types.py` | `Cell`, `Board`, `Move`, `CodebookMove`, `Variant`, `VariantMetadata` |
| `model/schema.py` | JSON schema version helpers; current version 2 |
| `solver/solver.py`, `solver/generator.py` | Solving, validation, seeded generation, uniqueness checks |
| `solver/variant_generators.py` | Variant layouts, cages, codebooks, and Kakuro generation |
| `solver/variant_search.py` | Bounded solution counting and clue removal for cages/runs/black cells |
| `services/validation.py` | Shared partial-board validation for rendering, Check Board, completion |
| `solver/one_to_25_templates.py` | Embedded templates for large-board generation |
| `services/` | Candidates, SE grading, text exchange, registry, timing, stats, history |
| `persistence/persistence.py` | JSON serialization, validation, atomic replacement, backup helpers |
| `ui/` | Grid rendering/input, generation dialog and workers, completion dialog, themes |

The controller owns session transitions. The UI emits `cell_selected`,
`value_entered`, and `pencil_toggled` signals and refreshes from controller state.
Workers in `ui/new_game_dialog.py` use Qt threads for variant generation and
cancellation. The dialog supplies metadata, puzzle, and solution to the shell. The controller
binds those results directly; it generates only when no pre-generated pair is supplied.

## Variant extension

`services/variant_registry.py` registers eight enum members. `register_variant()`
accepts a metadata factory and optional `constraint_ok` or `constraint_ok_factory`.
`resolve_constraint_ok(meta)` resolves a completed-grid callback (`Grid -> bool`).
Internal solver callbacks have their own signatures; check the caller before reuse.

The registry is an internal extension point. A new variant also needs model, solver,
candidate, persistence, UI, and test updates: these layers still contain explicit
variant branches. There is no external plug-in discovery or installation mechanism.

## Difficulty and hints

`grade(board, meta)` simulates techniques using fixed clues and returns a score and
label. It averages the applied step weights and caps the result at 8.0. A stalled
valid puzzle returns Extreme; a contradiction returns Invalid; an already complete
board returns Unknown. Larger/non-9×9 grids use a reduced technique set.

Generation levels are Easy/Medium/Hard/Expert; grading labels are
Easy/Medium/Hard/Extreme. The grader is separate from interactive hints.
Current hint modes and their limitations are documented in [USER_GUIDE.md](USER_GUIDE.md#hints).

## Persistence

`SaveState` holds board, variant metadata, optional solution, timer, stats,
SE score/label, hint limit, and original puzzle. The board carries player Codewords hypotheses. Saves write a temporary sibling and use `os.replace`;
an existing destination is copied to a `.bak` sibling first.

The JSON key is `version`. Versions 1 and 2 are accepted; all writes use version 2.
See [MIGRATIONS.md](MIGRATIONS.md) and [Appendix E](speckit.constitution.appendix.e.md)
for the exact structure and defaults. There is no database.

Undo history and theme/font preferences are not serialized. Loading clears history,
preserves saved candidates and derives remaining hints from the limit and usage.
A value edit recomputes candidates; candidate-only undo/redo preserves the exact edit.
`restore_backup(path)` loads the `.bak` sibling through the persistence API;
there is no dedicated restore-backup UI action.

## Text exchange

`services/text_format.py` exposes:

- `export_text(board_values, meta_dict, seed=0, difficulty="medium") -> str`
- `import_text(text) -> (board_values, meta_dict, seed, difficulty)`
- `export_puzzle_pack(puzzles, *, title=..., description="") -> str`
- `import_puzzle_pack(text) -> list[dict]`

The shell wires JSON/text Import/Export with atomic writes and visible errors. Text
imports have no saved solution and therefore no solution-based hints. JSON preserves
the session. There is no puzzle library UI; puzzle packs remain API-only.

## Future work

[IMPLEMENTATION_ISSUES.md](IMPLEMENTATION_ISSUES.md) tracks current integration gaps.
Puzzle editing, network sharing, cloud storage, multiplayer, and mobile layouts
remain future scope. Architecture requirements and rationale are in
[DECISIONS.md](DECISIONS.md) and [the constitution](speckit.constitution).
