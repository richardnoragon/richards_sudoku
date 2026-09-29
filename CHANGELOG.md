# Changelog

All notable changes to Sudoku-inator will be documented in this file.

The format is based on Keep a Changelog and is intended to be GitHub-friendly and easy to scan for release notes.

## Current status

The repository is currently in a stable, validated state for the implemented roadmap. Verification on the current codebase:

- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`
- Result: `583 passed, 2 warnings in 2.92s`

## [Unreleased]

### Added
- Public-facing branding update to Sudoku-inator
- GitHub documentation set for overview, architecture, and decisions
- Improved product-facing project documentation structure

### Changed
- README now reflects the Sudoku-inator product name
- Project metadata uses the public package name while preserving the internal compatibility package name

### Fixed
- Kept internal Python imports and runtime naming stable for existing code and tooling

---

## [0.1.0] - 2026-09-29

### Added
- Core desktop Sudoku experience with PyQt6
- Support for multiple puzzle variants:
  - Standard Sudoku
  - Jigsaw
  - Str8ts
  - Killer
  - 1to25
  - Codewords
  - KenKen
  - Kakuro
- Puzzle generation and validation logic
- Save/load persistence for game sessions
- Undo and redo support
- Hint and candidate assistance
- Difficulty grading and heuristic difficulty labels
- Keyboard-friendly UI and accessibility-focused status messaging
- Testing and linting infrastructure for local and CI validation

### Changed
- Project structure organized into modular controller, model, solver, services, persistence, and UI layers
- Gameplay logic normalized around a central controller-driven architecture

### Fixed
- Stabilized headless Qt test configuration for local and CI execution
- Improved validation around save state and variant constraints

---

## Notes

- The internal Python package remains `richards_sudoku` for compatibility with the existing codebase and tooling.
- The external product name is Sudoku-inator.
- This changelog is intended to serve as a concise release history for GitHub and contributor-facing documentation.
