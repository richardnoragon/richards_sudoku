# Sudoku-inator

Sudoku-inator is a Python + PyQt Sudoku app focused on rich variant support,
playability, and engineering reliability.

> The internal Python package name remains `richards_sudoku` for compatibility with the existing codebase and tooling, while the public-facing product name is Sudoku-inator.

## Current project status

This repository is currently in a stable beta-to-release-candidate state for the implemented feature set. The core gameplay, persistence, variant support, and release documentation are in place and have been validated against the repo’s real test suite.

Verified baseline:

- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`
- Result: `583 passed, 2 warnings in 2.92s`
- Supported variants: Standard Sudoku, Jigsaw, Str8ts, Killer, 1to25, Codewords, KenKen, and Kakuro
- Runtime baseline: Python 3.13+, PyQt6 desktop app

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
sudoku-inator
```

## First-Time User Onboarding

New users should start with the core workflow below:

1. Launch Sudoku-inator and choose a variant from the board setup flow.
2. Start with a familiar grid such as Standard Sudoku or Jigsaw before moving to more advanced layouts.
3. Use the status bar and hint guidance to understand available moves and puzzle progress.
4. Save regularly and keep the project backup guidance in mind when working with local game files.

For a deeper walkthrough, see [USER_GUIDE.md](USER_GUIDE.md).

## Contributing

We welcome bug reports, improvements, and variant work. For the contributor workflow, setup steps, testing expectations, and release checklist, see [CONTRIBUTING.md](CONTRIBUTING.md) and [RELEASE_PROCESS.md](RELEASE_PROCESS.md).

## Release Cadence and Roadmap

The project follows a milestone-based release model:

- stability and beta-grade reliability come first,
- variant maturity and validation follow,
- product polish and onboarding improve the user experience,
- extensibility and platform growth remain the longer-term architecture goal.

The active roadmap is tracked in [ROADMAP.md](ROADMAP.md), and release notes are maintained in [CHANGELOG.md](CHANGELOG.md).

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
