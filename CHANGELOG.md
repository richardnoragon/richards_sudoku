
> Development maturity is defined by [alpha.md](alpha.md); this archive supplies
> historical context and does not certify Alpha or Beta readiness.

# Changelog

## Alpha workflow implementation (Unreleased, 2026-10-01)

- Wired UI import/export and Check Board, added full-range F4 entry, and enabled
  hidden/editable Codewords hypotheses with history and JSON persistence.
- Fixed hint allowance/notes on load, original clues for Restart, save failure
  timer behavior, and unsaved-progress confirmation flows.
- Stabilized the five existing hint modes and removed obsolete fixture warnings.
- Fixed discarded worker results, invalid Str8ts/Killer output, and Kakuro worker
  API mismatch; added shared validation and bounded variant uniqueness search.
- Added regression coverage for variant lifecycles and failure recovery. Independent
  handoff and manual platform acceptance remain open; version remains 0.1.0.

All notable changes to Sudoku-inator will be documented in this file.

The format is based on Keep a Changelog and is intended to be GitHub-friendly and easy to scan for release notes.

## Current status

The package version is 0.1.0. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current
behavior and [TESTING.md](TESTING.md) for local validation. Release approval is pending;
the dated baseline below is not evidence of publication.

## [Unreleased]

### Full rebrand (2026-10-10)

- Renamed the internal Python package to `sudoku_inator`, updated imports, UI
  branding, contributor instructions, and the workspace to `sudoku-inator`.
- Retired the `richards-sudoku` command. Earlier naming notes below are historical
  and superseded by [REBRANDING.md](REBRANDING.md).
- Save schemas and application version remain unchanged.

### Added
- Public-facing branding update to Sudoku-inator
- GitHub documentation set for overview, architecture, and decisions
- Improved product-facing project documentation structure

### Changed
- Aligned project documents with the Alpha standard on 2026-10-01: recorded pre-alpha status, seven evidence criteria, stage-specific priorities, and DOC-09 independent handoff; package version and application behavior are unchanged.
- Aligned project status, requirements, roadmaps, user guidance, governance, and release evidence with the code on 2026-09-29.
- Replaced placeholder migration history with implemented schema v1/v2 compatibility and defaults.
- Documented open UI, hint, persistence, large-grid input, and Codewords gaps; separated archived design sketches from active documentation.
- README now reflects the Sudoku-inator product name
- Project metadata uses the public package name while preserving the internal compatibility package name

### Fixed
- Kept internal Python imports and runtime naming stable for existing code and tooling

---

## [0.1.0] - 2026-09-29 (development baseline; publication unverified)

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
- Keyboard navigation, digit entry for 1–9, and accessibility-focused status messaging; large-grid entry remains incomplete
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
