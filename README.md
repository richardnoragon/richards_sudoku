# richards_sudoku

richards_sudoku is a Python + PyQt Sudoku app focused on rich variant support,
playability, and engineering reliability.

## What You Can Play

- Standard Sudoku (9x9)
- Jigsaw
- Str8ts
- Killer
- 1to25
- Codewords
- KenKen
- Kakuro

## Quick Start (Windows / macOS / Linux)

1. Create and activate a Python 3.13 environment.
2. Install the project in editable mode with dev dependencies.
3. Run the desktop app.

```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
richards-sudoku
```

## Phase 0 UX Improvements

The app has completed the initial UX/accessibility foundation for the current release cycle:

- Clearer selected-cell feedback and stronger status messaging in the board UI.
- Keyboard-first guidance surfaced in the status bar for navigation and input actions.
- Improved accessibility hooks through focusable controls and meaningful labels.
- More readable action descriptions and tooltips for common gameplay tasks.
- A consistent design direction aligned with the product UX spec for future variant work.

## Design Direction

See [UX_DESIGN_SPEC.md](UX_DESIGN_SPEC.md) for the current product-facing design direction, user journeys, information architecture, accessibility requirements, and success criteria.

## Run Tests

```bash
QT_QPA_PLATFORM=offscreen pytest -q
```

The PyQt6 test backend is configured explicitly for headless CI/local runs so the Qt plugin does not fall back to the incompatible PySide6 bindings.

## Quality Gates (Local)

Run the same checks used by CI before opening a PR:

```bash
ruff check src
mypy
pytest -q
```

## Project Tracking

- Todo/status source: `speckit.tasks`
- Milestone/status overview: `milestone_roadmap.md`
- Release gate: `RELEASE_CHECKLIST.md`
- Phase 1 MVP baseline: complete in this branch
- Phase 2 Beta baseline: complete in this branch
- Phase 3 persistence baseline: complete in this branch
- Phase 4 extended-variant baseline: complete in this branch
- SE difficulty grader advanced techniques: complete in this branch
