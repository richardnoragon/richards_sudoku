# Contributing to Sudoku-inator

Thanks for helping improve Sudoku-inator. This project values small, well-tested changes and a clear path from local experimentation to release-ready contributions.

## Project conventions

- The public product name is Sudoku-inator.
- The internal Python package remains `richards_sudoku` for compatibility with the existing codebase and tooling.
- Repository docs, release notes, and roadmap updates should stay aligned with the current state of the project.

## Local setup

Use Python 3.13+ and install the project in editable mode with the dev tooling:

```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

For the Qt desktop app, the test environment should use headless execution when running locally or in CI:

```bash
QT_QPA_PLATFORM=offscreen pytest -q
```

## Working style

- Keep changes focused and scoped to the relevant feature or bug.
- Prefer targeted tests for the behavior being changed.
- Update user-facing docs when the behavior, release flow, or product messaging changes.
- Preserve versioned persistence compatibility when changing save/load behavior.

## Validation before opening a PR

Run the repository checks that are most relevant to your change:

```bash
ruff check src
mypy
pytest -q
```

For UI-related changes, prefer the headless Qt flow above so the app can be exercised without a desktop display.

## Release and roadmap expectations

- Keep the roadmap and the changelog current with actual shipped work.
- Review [RELEASE_PROCESS.md](RELEASE_PROCESS.md) before final release decisions.
- Keep user-facing docs in sync with the current release state.

## Reporting issues

- For product flaws or bugs, open an issue with a reproduction path and expected behavior.
- For security concerns, follow the guidance in [SECURITY.md](SECURITY.md).

## Pull requests

A strong PR should include:

- a clear summary of the change,
- the problem or user need being addressed,
- validation evidence from the relevant tests,
- any note about migration, compatibility, or UX impact.

Thank you for helping make Sudoku-inator more reliable, more usable, and more extensible.
