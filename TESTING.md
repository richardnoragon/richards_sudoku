# Testing

This document describes the testing approach for Sudoku-inator. It is intended to support continuous validation, release readiness, and regression protection across the project’s Python and PyQt6 codebase.

## Current verified status

The project is currently validated on the mainline branch with the following real regression run:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest -q
```

Result: `583 passed, 2 warnings in 2.92s`

The currently reported warnings are non-blocking pytest deprecation warnings from the class-scoped performance fixture and do not indicate a product-level failure.

## Test strategy

The project uses a layered test model intended to verify correctness at the right level without slowing development.

### 1. Unit tests
Unit tests validate the behavior of isolated functions and domain logic without a full UI lifecycle. These tests cover:

- puzzle generation and validation
- solver correctness and constraints
- candidate generation and elimination rules
- difficulty calculation and scoring logic
- persistence serialization/deserialization
- helpers for formatting, history, and timers

The project’s primary test runner is `pytest`, configured in `pyproject.toml` to discover files under `tests/` and run functions named `test_*`.

Typical command:

```bash
pytest
```

For a narrower run during development:

```bash
pytest tests/test_model_types.py
pytest tests/test_solver.py
```

### 2. Integration tests
Integration tests validate interactions between major application layers, such as:

- controller and model coordination
- save/load workflow against real state objects
- solver input flowing through service logic
- UI actions invoking the underlying controller behavior

These tests are critical because the application is made up of multiple modules that must work together consistently.

### 3. UI tests
The project includes Qt-focused tests for UI behavior where appropriate, using `pytest-qt` and the PyQt6 integration layer.

Examples include:

- menu and action wiring
- form field and widget behavior
- status feedback and UI state transitions
- application startup and shell construction

Recommended commands:

```bash
pytest -m qt
```

When headless CI environments are being used, the application should be validated with the display configuration required by the Qt test harness.

### 4. Performance and stability checks
The project also includes performance-oriented validation for long-running or resource-sensitive workflows. These checks help ensure solver and generation tasks stay within acceptable limits and do not regress significantly over time.

Example:

```bash
pytest tests/test_performance.py
```

### 5. Static validation
Static validation complements testing and should be run before release-quality merges.

- Ruff for linting
- Mypy for type checking

Typical commands:

```bash
ruff check .
mypy src/richards_sudoku/model
```

## Acceptance tests

Acceptance tests represent the user-facing behaviors that must work in a real session. They are designed to confirm that the product delivers the intended result from a gameplay and UX standpoint.

### Core acceptance scenarios

1. New game creation
   - A valid puzzle is generated for the selected variant.
   - The board initializes in a consistent state.
   - The timer, status, and metadata start correctly.

2. Puzzle completion
   - A correctly solved board is recognized as complete.
   - The completion state updates UI status and relevant metrics.

3. Hint usage
   - A hint reveals a valid answer without corrupting the board state.
   - Hint limits and counters behave as expected.

4. Save and restore
   - A game can be saved and reopened without losing board state or metadata.
   - Versioning and persistence logic remain backward compatible when possible.

5. Undo and redo
   - User actions can be reversed and re-applied in order.
   - Undo history respects the correct game state transitions.

6. Variant-specific behavior
   - Standard Sudoku rules remain enforced.
   - Variant-specific logic for Jigsaw, Str8ts, KenKen, Kakuro, Codewords, Killer, and 1-to-25 behaves correctly.

7. User-facing reliability
   - UI actions do not crash on repeated use.
   - Status messages are understandable and consistent.
   - The application remains responsive during common operations.

Acceptance tests should be treated as the minimum quality gate for functional readiness.

## Regression testing

Regression testing is used to confirm that previously fixed defects remain fixed and that new changes do not reintroduce old failures.

### Regression principles

- Every bug fix should include or update a focused automated test whenever possible.
- Critical user paths should be tested at least once in both unit-level and integration-level coverage.
- Fixes affecting persistence, solver logic, or UI flows require expanded validation beyond the narrow test.

### Recommended regression workflow

1. Identify the bug or behavior change.
2. Write a failing test that captures the original issue.
3. Implement the fix.
4. Run the smallest relevant test subset first.
5. Run the broader related suite for confidence.
6. Confirm the fix does not regress adjacent behavior.

Examples of regression-sensitive areas:

- solver constraint validation
- difficulty calculation
- save/load compatibility
- variant selection logic
- board analytics and candidate generation
- PyQt action wiring

## Disposable library testing

Disposable library testing refers to validating logic, integrations, or helper libraries that may be temporary, experimental, or intentionally isolated from the core runtime. In this project, the intent is to test behavior in a controlled, replaceable way without depending on long-lived production assumptions.

### Goals

- Validate a component before it becomes a permanent dependency.
- Keep third-party or disposable helper integrations isolated from core gameplay logic.
- Ensure experimental features can be removed or replaced without destabilizing the application.

### Approach

- Test the library behind a small, stable interface.
- Treat the library as a dependency boundary, not as the app’s core logic source of truth.
- Validate expected inputs and outputs in isolation.
- Verify error handling, timeouts, and fallback behavior.
- Confirm no hidden state survives between tests.

### Good patterns

- Use fresh fixtures for each test case.
- Prepare minimal in-memory data instead of reusing global application state.
- Prefer deterministic fixtures over runtime-dependent randomness.
- Keep disposable libraries behind wrappers when they may be removed later.

### Example checks

- library can parse valid puzzle data
- invalid state is rejected gracefully
- failure modes produce predictable exceptions or fallback behavior
- performance remains acceptable under repeated use

This gives the project a safer path for integrating experimental utilities while keeping the production codebase stable.

## Release validation

Release validation is the final quality gate before publishing or tagging a build. It confirms the project is ready for distribution and the public-facing experience is stable.

### Release checklist

Before release, all of the following should be verified:

1. Full test suite passes
   ```bash
   pytest
   ```

2. Linting passes
   ```bash
   ruff check .
   ```

3. Type checks pass for the relevant modules
   ```bash
   mypy src/richards_sudoku/model
   ```

4. Core UI flows work in the packaged application
   - launch app successfully
   - open a new puzzle
   - solve or validate standard flows
   - save and reload

5. Packaging metadata is valid
   - project name and version are correct
   - entry points resolve correctly
   - dependencies install without conflict

6. Regression sweeps are complete
   - all known bug-fix tests pass
   - no recent solver or persistence regressions remain

7. Documentation is current
   - README reflects product state
   - architecture and testing docs are up to date
   - changelog entries are accurate for the release

### Release smoke test

A minimal release smoke test should cover:

- application launches
- game starts successfully
- one representative variant loads and is playable
- a save file can be restored
- a core validation path succeeds without crash

### Exit criteria

A release is ready only when:

- the full test suite passes,
- compatibility and packaging checks pass,
- acceptance scenarios pass,
- known regressions are either fixed or explicitly documented,
- and the current build has been manually checked in a real runtime environment.

## Summary

The testing model for Sudoku-inator combines unit coverage, integration checks, Qt validation, regression protection, and release-level verification. This structure keeps the product stable while allowing new features and puzzle variants to be introduced with confidence.
