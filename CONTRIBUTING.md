# Contributing to Sudoku-inator

## Independent Alpha handoff (DOC-09)

A different developer must complete this exercise using written repository guidance
without direct assistance from the original author. Record problems as issues and
improve the instructions before repeating affected steps. The standard is [alpha.md](alpha.md).

1. Clone the repository from its hosting URL and record the checked-out revision
   (`git rev-parse HEAD`), OS, Python version, and tester identity.
2. Follow [README.md](README.md#install-and-run) in a fresh virtual environment;
   install `.[dev]`, build a wheel with `python -m pip wheel --no-deps . -w dist`,
   and verify the wheel installs and launches in a separate clean environment.
3. Launch `sudoku-inator` in a desktop session. Follow [USER_GUIDE.md](USER_GUIDE.md)
   through the primary workflows and record limitations or failures.
4. Run the [documented checks](TESTING.md#setup-and-commands) and retain commands,
   outputs, dependency versions, and any setup corrections.
5. Use [ARCHITECTURE.md](ARCHITECTURE.md) and [DECISIONS.md](DECISIONS.md) to locate
   the relevant code. Make a small change and verify it with an appropriate check.
6. Review module boundaries, configuration, save storage, and extension contracts;
   record whether any major rewrite is expected and why.
7. Add the dated record to TESTING.md or linked review evidence, including all
   assistance needed. Update DOC-09 and the Alpha checklist only when demonstrated.

This exercise is still pending; the presence of these instructions is not a completed handoff.

See [DOCUMENTATION.md](DOCUMENTATION.md) for document ownership and
[PROJECT_STATUS.md](PROJECT_STATUS.md) for current gaps. Use the [README](README.md#install-and-run)
virtual-environment setup and [TESTING.md](TESTING.md) for Windows commands and CI scope.


Thanks for helping improve Sudoku-inator. This project values small, well-tested changes and a clear path from local experimentation to release-ready contributions.

## Project conventions

- The public product name is Sudoku-inator.
- The Python package is `sudoku_inator`; use it in imports and module paths. See [REBRANDING.md](REBRANDING.md) for migration instructions.
- Repository docs, release notes, and roadmap updates should stay aligned with the current state of the project.

## Local setup

Use Python 3.13+ and install the project in editable mode with the dev tooling:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
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
python -m ruff check src
python -m mypy
QT_QPA_PLATFORM=offscreen python -m pytest -q
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
