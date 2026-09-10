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

## Planned UX Improvements

The project should continue improving the player experience with these priorities:

- Improve visual feedback for selection, conflicts, and variant rules.
- Raise accessibility through better contrast, font scaling, and keyboard-first navigation.
- Reduce onboarding friction with brief in-app guidance and clearer status messages.
- Standardize dialogs, menus, and controls to make the interface more predictable.
- Add lightweight tutorials and contextual help for advanced variants without overwhelming new users.

## Design Direction

See [UX_DESIGN_SPEC.md](UX_DESIGN_SPEC.md) for the current product-facing design direction, user journeys, information architecture, accessibility requirements, and success criteria.

## Run Tests

```bash
pytest -q
```

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
