# Testing

## Alpha evidence requirements

The [Alpha standard](alpha.md) requires tests for major workflows plus an independent
handoff. The 2026-10-01 implementation pass adds regression evidence below;
the earlier 2026-09-29 results are retained as historical evidence.

For an Alpha candidate record revision, platform, dependency versions, tester,
commands, outcomes, and failures. Cover generation/play/completion, all enabled
variant input paths, hints, pencil marks, undo/redo, restart, save/reopen/resume,
UI import/export/check, malformed files, backup recovery, and unsaved transitions.
Link regression checks for DOC-01–06 to that evidence. Record the DOC-09 exercise
from [CONTRIBUTING.md](CONTRIBUTING.md#independent-alpha-handoff-doc-09), including
architecture review and the small verified change. No independent handoff record
or manual cross-platform acceptance record is currently available.

Promote only after all [seven criteria](PROJECT_STATUS.md#alpha-readiness) are met.
Beta needs ordinary-user reliability evidence; publication also needs current
platform CI, governance, and release approvals.

## Latest local validation

Implementation pass on **2026-10-01**, working tree based on `2149d7d`.
Tester: the implementing Codex agent; this is not the independent DOC-09 handoff.

- Final installed-wheel pytest result: **614 passed in 15.59s; no warnings**.
- Ruff (`python3 -m ruff check src`): passed.
- Mypy (`python3 -m mypy`): passed for the three configured model files.
- Markdown lint: passed for all 155 Markdown files; maintained-document local file
  links checked after the documentation update.
- DOC-08's two fixture deprecation warnings are absent.

### Clean installed-wheel verification

Built `sudoku_inator-0.1.0-py3-none-any.whl`, installed it into an isolated temporary
virtual environment, copied the tests/config outside the checkout, and ran pytest
there. The imported package path was checked to belong to that environment.
Runtime: Linux, Python 3.14.4, PyQt6 6.11.0, Qt build 6.11.0 (Qt6 distribution 6.11.2), pytest 9.1.1, pytest-qt 4.5.0.

The host lacks `ensurepip`, so `python3 -m venv` reported the missing venv package.
For this check, pip's `--python <temporary-env>/bin/python` option installed the wheel
and test dependencies into the isolated interpreter. README documents the normal
fix: install the distribution's matching Python venv package. No global Python
packages or system packages were changed.

Reproduction after creating an isolated environment:

```bash
python3 -m pip wheel --no-deps . --wheel-dir /tmp/sudoku-wheels
# Install the wheel and test dependencies in that environment, then copy tests
# and pyproject.toml to an external directory and run from there:
QT_QPA_PLATFORM=offscreen /path/to/environment/bin/python -m pytest tests -q
```

An offscreen QApplication smoke check constructed and showed MainWindow, ran the
event loop, and closed successfully. Both CLI entry points are installed.
This verifies installation and startup; desktop rendering and human usability
still need manual acceptance on supported platforms.

### Added regression coverage

`tests/test_alpha_workflows.py` covers:

- UI text import/export, Check Board, failed import, and generated-dialog handoff.
- JSON restore of hints, notes, original clues, Codewords hypotheses, and legacy defaults.
- Atomic replace failure, unchanged previous save/backup, and cleanup of temporary files.
- Save/Discard/Cancel transitions, including cancelled/failed saves.
- F4 value 25, pencil mode, deletion, undo/redo; hidden/locked/editable codebook fields.
- Elimination history, unknown hints, and fixed-reveal history safety.
- Worker → play → save → load → completion → restart for all variants, including
  KenKen 4×4/6×6/9×9 and the hard 25×25 template path (seed 42).
- Bounded uniqueness proof for generated Str8ts, Killer, KenKen, and Kakuro;
  explicit ambiguous/unique/invalid Kakuro fixtures and cancelled/exhausted search.
- Undoing completion resumes timing; redoing the final move triggers completion.

No current GitHub CI/ruleset checks, manual desktop/platform sessions, release
approvals, or independent developer handoff were performed. DOC-06 manual
accessibility, DOC-07 platform acceptance, and DOC-09 remain open.

## Historical local validation (2026-09-29)

Run on 2026-09-29 against the working tree based on `2149d7d`, on Linux with
Python 3.14.4 and the installed PyQt6 environment:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest -q
python3 -m ruff check src
python3 -m mypy
```

- Pytest: **583 passed, 2 warnings in 2.64s**.
- Ruff: all checks passed.
- Mypy: no issues in the three configured model files.
- The two `PytestRemovedIn10Warning` warnings concern an instance-method,
  class-scoped fixture in `tests/test_performance.py`. Tracked as DOC-08.

At that review, manual gameplay, fresh installation, current remote CI, and branch
protection still required release evidence. The newer local install results below
supersede the local-install gap only. See
[PROJECT_STATUS.md](PROJECT_STATUS.md) and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).
The existing `.venv` lacked pytest during this review; commands above used `python3`.

## Setup and commands

Create an environment and install `.[dev]` as described in [README.md](README.md).
Use the same environment for the app, tests, Ruff, and mypy.

```bash
python -m ruff check src
python -m mypy
```

Linux/macOS headless tests:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q
```

Windows PowerShell:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
```

Pytest explicitly selects PyQt6 via `qt_api = "pyqt6"` in `pyproject.toml`.
For focused runs, set the same Qt environment and run, for example:

```bash
python -m pytest tests/test_solver.py tests/test_persistence.py -q
python -m pytest tests/test_ui_shell.py tests/test_wiring.py -q
python -m pytest tests/test_performance.py -q
```

## Coverage and boundaries

The suite covers models, solver/generator behavior, variant constraints, candidates,
difficulty grading, persistence, text exchange, services, UI shell, and controller
wiring. Passing API tests do not prove a menu action is connected or that every
acceptance requirement is met. Open UI gaps are listed in PROJECT_STATUS.md.

The performance suite uses wall-clock assertions and fixed fixtures. Budgets are
in [Appendix D](speckit.constitution.appendix.d.md). There is no configured
pytest-benchmark dependency, historical regression dashboard, or automated memory gate.

## CI scope

[Quality Gates](.github/workflows/quality-gates.yml) runs on pull requests and pushes
to `main`, using Python 3.13:

| Job | Check |
| --- | --- |
| Markdown Lint | `**/*.md` with `.markdownlint-cli2.jsonc` |
| Python Lint and Type | `ruff check src`, then `mypy` |
| Tests (ubuntu-latest) | `xvfb-run -a pytest -q`, offscreen Qt |
| Tests (windows-latest) | `pytest -q`, offscreen Qt |
| Tests (macos-latest) | `pytest -q`, offscreen Qt |

Ruff currently selects E9, F63, F7, F82; import sorting is not enabled.
Mypy checks `src/sudoku_inator/model`, not the entire application.
Markdown lint has multiple disabled rules; lint success does not validate links,
factual accuracy, or governance compliance. Run it locally with:

```bash
npx --yes markdownlint-cli2 '**/*.md'
```

## Release acceptance

Record fresh environment installation, launch, generation, keyboard/mouse play,
completion, hints, undo/redo, restart, and save/reload for the release commit.
Exercise all enabled variants, especially large-board entry and Codewords.
Verify error recovery, accessibility, and unsaved-progress handling manually.
Attach the platform CI runs and resolve or explicitly defer each open gap before
marking the [release checklist](RELEASE_CHECKLIST.md) complete.
