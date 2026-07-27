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
- Milestone/status overview: `milestone_raodmap.md`
- Release gate: `RELEASE_CHECKLIST.md`
