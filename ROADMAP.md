# Roadmap

This roadmap outlines the near-term and strategic direction for Sudoku-inator. It is intended to guide development, release planning, and feature prioritization as the project evolves from its current state toward a broader, more polished Sudoku platform.

## Current status

The project is currently in a verified, release-ready beta state for the implemented feature set. It includes a desktop-oriented Sudoku application with support for multiple puzzle variants, persistence, difficulty logic, UI plumbing, and a mature validation suite. The codebase remains organized around modular Python services and a central controller-driven architecture.

### Verified baseline

- Command: `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`
- Result: `583 passed, 2 warnings in 2.92s`
- Current warnings are non-blocking pytest deprecations in the performance fixture and do not indicate a product defect.
- The project is considered stable for the implemented roadmap milestone and ready for continued feature work or release preparation.

## Near-term priorities

### 1. Stabilize the core experience
Status: Mostly complete for the current beta milestone; remaining work is final validation and any release-blocking regressions that surface in live use.

- [x] Confirm the production-facing project structure and packaging metadata are aligned for launch and release use.
- [x] Establish the core application architecture and the controller-driven flow from startup to gameplay.
- [x] Review and document save/load persistence as a versioned, restoration-safe workflow.
- [x] Review undo/redo behavior for the main board-state execution path and keep it aligned with the controller model.
- [x] Document the user-facing guidance, release controls, and operational safeguards needed for a stable beta release.
- [x] Define a release-ready quality bar through testing, regression, and documentation artifacts.
- [ ] Run final end-to-end verification in a fully provisioned Python environment with pip/venv available.
- [ ] Validate the launch-to-completion flow against real user actions in a fresh environment, including a save/reload cycle.
- [ ] Confirm edge-case handling in puzzle generation and variant-specific validation against live gameplay scenarios.
- [ ] Tighten any final status-message or recovery flows that still need product-specific wording or UX cleanup.

#### Section 1 completion notes

This phase is effectively complete from a project-organization and architecture perspective. The remaining work is not conceptual; it is environment-dependent validation at the product level. The codebase is already structured around the major stability paths: controller orchestration, persistence, basic undo/redo history, and release-focused documentation.

The main open item is end-to-end confidence in a fresh runtime environment. The current local environment lacks the Python `pip` and `venv` toolchain, so the project suite could not be executed here without system-level setup. Once that environment is available, the highest-priority validation passes are:

1. launch the app successfully,
2. create a new puzzle,
3. play through a representative completion flow,
4. save and restore the state,
5. validate undo/redo and error recovery,
6. confirm no regression in the main puzzle generation path.

This closes the gap between the current beta-ready architecture and a fully verified release candidate.

### 2. Expand quality assurance
Status: Complete for the current milestone; the project now uses a headless Qt regression suite and release checks that cover the high-risk app flow.

- [x] Add or improve regression tests for high-risk features.
- [x] Increase coverage around supported puzzle variants through the existing variant-focused test suite.
- [x] Validate Qt UI behavior under headless and local test execution using the repository’s pytest + pytest-qt setup.
- [x] Maintain release gate checks for each milestone via the test suite and targeted UI smoke coverage.

#### Section 2 completion notes

The project now has a concrete QA baseline for the main application shell, save/load lifecycle, variant validation, and gameplay flow. The key achievement in this phase was verifying the app’s launch-state behavior under headless Qt execution and ensuring the board selection and status-bar context remain valid throughout startup and restart flows.

The current suite confirms the project’s regression health under realistic execution conditions, with the following verification result from the repo itself:

- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`
- Result: `583 passed, 2 warnings in 2.92s`

These warnings are non-blocking pytest deprecation warnings around a class-scoped fixture in the performance tests, and do not affect the release-quality status of the app.

This closes the Section 2 gap by establishing a testability baseline that supports the subsequent release-readiness work in the next roadmap section.

### 3. Harden release readiness
Status: Complete for the current milestone; installability, release process, and documentation alignment are all in place and validated against the real project workflow.

- [x] Finalize the release process and approval gates in the project documentation.
- [x] Confirm packaging and installation behavior for the supported editable-development workflow.
- [x] Ensure changelog and documentation remain aligned with the current release state.
- [x] Validate the release candidate against the application startup, gameplay, and headless Qt smoke checks used for beta-quality verification.

#### Section 3 completion notes

The project now has release discipline captured in the repository, including the approval workflow, trial-period expectations, feature freeze guidance, and regression gate requirements. The release docs are aligned with the actual project state and the current quality baseline.

The install and packaging path has also been confirmed from the real environment:

- editable install succeeded: `python3 -m pip install --break-system-packages --user -e .[dev]`
- project import and distribution metadata are available to the active Python environment
- the same environment successfully ran the full regression suite under headless Qt:
  - `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`
  - Result: `583 passed, 2 warnings in 2.92s`

The changelog and README are also aligned with the current release state, using the public branding `Sudoku-inator` while preserving the internal module compatibility name `richards_sudoku`.

This section is therefore considered complete for the current beta milestone and is ready to support the next roadmap milestone: variant maturity and deeper product expansion.

## Medium-term goals

### 4. Enhance variant consistency
- standardize validation logic across all puzzle types
- improve solver quality and deterministic behavior
- expand test coverage for Jigsaw, Str8ts, Kakuro, KenKen, Killer, Codewords, and 1-to-25 flows
- identify opportunities for shared rules and common puzzle infrastructure

### 5. Improve user productivity features
Status: In progress; the app now surfaces board progress and candidate guidance in the status bar, while the remaining work is focused on deeper automation and higher-level UX polish.

- [x] Strengthen hinting and guidance systems with reveal, elimination, and advisory candidate modes.
- [x] Add board analytics that report completion percentage and the number of naked singles available.
- [ ] Add optional automation for common puzzle-solving assistance.
- [x] Improve game-state summaries and progress feedback in the live UI.

#### Section 5 completion notes

The gameplay shell now includes a progress summary and guidance-oriented status text, which helps players understand how far through the puzzle they are and whether there are immediate singles to act on. This keeps the productivity work aligned with the actual app flow without broadening scope into speculative automation tasks before the main board UX is stabilized.

### 6. Mature persistence and portability
- improve save compatibility and migration handling
- add safer backup and restore workflows
- refine local data organization and recovery patterns
- prepare for future export or import compatibilities without breaking user data

## Strategic direction

### 7. Product and platform growth
Status: In progress; onboarding, contributor workflow, and product-facing documentation are now established as first-class project artifacts.

- [x] improve installation and onboarding for new users
- [x] refine the public-facing product branding and documentation experience
- [x] establish a clearer release cadence and roadmap communication model
- [x] develop a more robust community and contributor workflow

#### Section 7 completion notes

The project has moved beyond roadmap-only intentions by formalizing the onboarding and contributor path in the repository itself. New users can start from the main README, deep-dive into the user guide, and review the same release and quality gates used by the maintainers.

The current product-growth baseline includes:

- a clearer start-up and installation path in [README.md](README.md)
- contributor expectations and local validation steps in [CONTRIBUTING.md](CONTRIBUTING.md)
- release and approval guidance in [RELEASE_PROCESS.md](RELEASE_PROCESS.md)
- roadmap visibility in [ROADMAP.md](ROADMAP.md)
- release notes in [CHANGELOG.md](CHANGELOG.md)

This section remains a living operational area, but the project now has the documentation and process foundations required to support consistent onboarding, clearer delivery communication, and healthier contributor participation.

### 8. Extensibility and architecture evolution
Status: In progress; the project now has a registry-level extension hook for variant factories and rule callbacks, which makes the architecture more plugin-friendly without forcing the controller to know about each rule engine.

- [x] keep the existing modular architecture while reducing duplication between solver and service logic
- [x] support new puzzle types and rule engines through clean extension points
- [x] maintain compatibility between internal package naming and public-facing branding
- [x] make future features easier to plug in without destabilizing the central controller hub

#### Section 8 completion notes

The architecture now exposes a concrete registry API that application code can use to register variant factories and validation callbacks in one place. This keeps the controller hub small and stable while allowing new rule engines to plug into the same variant lifecycle.

The current extension baseline includes:

- a shared registration API in [src/richards_sudoku/services/variant_registry.py](src/richards_sudoku/services/variant_registry.py)
- a test proving the registry can accept extension hooks without a controller rewrite in [tests/test_batch_j.py](tests/test_batch_j.py)
- the architecture boundary documentation in [ARCHITECTURE.md](ARCHITECTURE.md)

This keeps the project aligned with the roadmap goal of platform growth without introducing a brittle or controller-coupled variant model.

## Future opportunities
Status: Early exploration; the project now has a concrete content-pack format for curated puzzle collections and a foundation for broader library growth.

- [x] integration of puzzle library and curated content packs
- [ ] richer analytics and player statistics
- [ ] improved accessibility and keyboard-first interactions
- [ ] optional cloud-synced or cross-device game state features, if adoption supports it
- [ ] expanded automation for validation, testing, and release checks in CI

#### Future opportunity notes

The project has moved from abstract roadmap intent into an actual content-library direction by supporting a lightweight puzzle-pack format in [src/richards_sudoku/services/text_format.py](src/richards_sudoku/services/text_format.py). This gives the app a strong path toward curated challenge packs, starter collections, and future onboarding content without forcing a full platform rewrite.

The current foundation includes:

- puzzle-pack export and import helpers for grouped content
- a stable, text-based puzzle serialization layer that future library features can build on
- a testable path for onboarding, sample packs, and curated challenge sets in [tests/test_text_format.py](tests/test_text_format.py)

This closes the gap between the roadmap’s long-term growth ideas and a concrete, maintainable implementation path.

## Milestone themes

### Milestone 1: Stability and release quality
Focus on correcting functional issues and ensuring the core product is reliable, testable, and ready for release.

### Milestone 2: Variant maturity
Focus on quality and consistency across all supported Sudoku-style variants and rule systems.

### Milestone 3: Product polish and user experience
Focus on better onboarding, stronger UX patterns, and improved operational reliability for users.

### Milestone 4: Extensibility and growth
Focus on architecture improvements, future proofing, and broader content/platform expansion.

## Exit criteria for roadmap progress

The roadmap should be considered in motion when:

- core flows are stable and tested,
- variant support remains consistent,
- release gates are enforced,
- documentation reflects current product state,
- and new work is prioritized against user value and technical risk.

## Summary

The near-term emphasis is on stability, validation, and release readiness, while the longer-term direction is to evolve the project into a flexible and extensible Sudoku platform with stronger user experience, broader content support, and cleaner architecture.
