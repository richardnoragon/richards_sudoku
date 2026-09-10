# Implementation Issues by Workstream

This document groups the current project backlog into implementation-oriented workstreams for the existing Python + PyQt Sudoku app. The groups align with the project’s current MVP, Beta, and extended-variant roadmap in the repository and should be executed in dependency order.

## Phase 0 — UI/UX and Accessibility Baseline

### Issue 0: Improve UI/UX and accessibility experience
**Goal:** Reduce friction for new and returning players while improving clarity, confidence, and comfort during gameplay.

**Recommended UX improvements**
- Strengthen visual feedback for selected cells, conflict states, candidate modes, and variant rules.
- Improve keyboard navigation, focus retention, and screen-reader-friendly labeling.
- Increase contrast and legibility across light/dark themes and larger/smaller displays.
- Add contextual guidance for game actions, new-game setup, and variant-specific rule explanations.
- Reduce modal overload by favoring concise, readable dialogs and inline status feedback.
- Standardize menu labels, dialog layouts, and control grouping so the app feels consistent and intuitive.
- Add onboarding guidance for first-time users, including short tooltips, tutorial steps, or a quick start overlay.
- Ensure destructive actions such as restart or overwrite are clearly confirmed and easy to reverse.

This body of work should follow the UX direction defined in [UX_DESIGN_SPEC.md](UX_DESIGN_SPEC.md), especially the principles of board-first clarity, calm interaction patterns, and accessibility-first behavior.

**Acceptance criteria**
- The app feels easier to learn and easier to use during a normal session.
- Important actions have visible states and clear feedback.
- The interface remains usable with keyboard input and readable under accessibility-focused settings.
- New-game and variant-selection flows offer enough clarity for players without prior knowledge.

**Relevant files**
- `src/richards_sudoku/ui/grid_widget.py`
- `src/richards_sudoku/ui/new_game_dialog.py`
- `src/richards_sudoku/ui/theme.py`
- `src/richards_sudoku/main.py`
- `README.md`

---

## Phase 1 — Core App Baseline

### Issue 1: Deliver the playable MVP game loop
**Goal:** Complete the standard Sudoku gameplay loop from new game through completion.

**Scope**
- Standard 9x9 puzzle generation and validation
- Cell selection, keyboard/mouse input, and conflict highlighting
- Undo/redo, timers, and basic stats tracking
- Save/load and local persistence
- Light/dark UI shell and polishing for a usable first release

**Acceptance criteria**
- A user can start a new standard puzzle, play it to completion, and save/load progress.
- Keyboard and mouse controls work reliably.
- Timer, statistics, and save/load round-trips are stable.
- The UI matches the project’s MVP goals without regressions.

**Relevant files**
- `src/richards_sudoku/controller/game_controller.py`
- `src/richards_sudoku/ui/grid_widget.py`
- `src/richards_sudoku/persistence/persistence.py`
- `src/richards_sudoku/main.py`

---

### Issue 2: Complete gameplay assistance and quality-of-life features
**Goal:** Add the mature assistance layer expected by the MVP/Beta milestone.

**Scope**
- Pencil marks and candidate editing
- Hint modes and hint limits
- Conflict detection and selected-cell highlighting
- Game-complete dialog and improved UI feedback
- Restart/reset actions and consistency across sessions

**Acceptance criteria**
- The user can use hints, pencil marks, and undo/redo without breaking board state.
- Hint-limit logic reflects the configured game policy.
- The game completion flow is visible and user-friendly.
- Restart actions behave predictably without corrupting saved state.

**Relevant files**
- `src/richards_sudoku/services/candidates.py`
- `src/richards_sudoku/ui/new_game_dialog.py`
- `src/richards_sudoku/ui/game_complete_dialog.py`
- `tests/test_ui_shell.py`

---

## Phase 2 — Variant Expansion and Difficulty Engine

### Issue 3: Expand the variant engine and generator framework
**Goal:** Deliver the supported Beta variants through a reusable generator and metadata pipeline.

**Scope**
- Jigsaw, Str8ts, and Killer generator support
- Constraint-aware generation and uniqueness validation
- Variant registry and generator hooks
- Difficulty-aware clue density and metadata handling

**Acceptance criteria**
- Each Beta variant can generate a playable board and complete a full game flow.
- Variant-specific restrictions are enforced during generation and candidate evaluation.
- The generator continues to respect cancellation and uniqueness checks.
- Tests cover generation invariants and variant-specific edge cases.

**Relevant files**
- `src/richards_sudoku/solver/generator.py`
- `src/richards_sudoku/solver/variant_generators.py`
- `src/richards_sudoku/services/variant_registry.py`
- `tests/test_variant_generators.py`

---

### Issue 4: Mature the SukakuExplainer difficulty and cell evaluation pipeline
**Goal:** Make puzzle difficulty ratings consistent, explainable, and variant-aware.

**Scope**
- Extend `_WorkingGrid` and technique registry for variant-specific constraints
- Tune weight and scoring thresholds for Easy/Medium/Hard/Extreme
- Validate Str8ts and Killer-specific candidate elimination
- Expose difficulty information to the status bar and persisted save state

**Acceptance criteria**
- Difficulty labels remain stable and interpretable across variants.
- Killer and Str8ts constraints are reflected in grading decisions.
- SE scoring is surfaced in the UI and persisted with saves.
- The performance budget for grading remains within project thresholds.

**Relevant files**
- `src/richards_sudoku/services/difficulty_se.py`
- `tests/test_difficulty_se.py`
- `tests/test_performance.py`

---

## Phase 3 — Data Integrity and Persistence

### Issue 5: Harden persistence and import/export for all supported variants
**Goal:** Ensure save/load and puzzle import/export remain trustworthy across variant changes.

**Scope**
- Versioned save formats and schema safety checks
- Validation for Jigsaw, Str8ts, and Killer metadata on load
- Import/export support for custom board formats and repeating-field metadata
- Error surfacing to the user without crashing the app

**Acceptance criteria**
- Save/load round-trips preserve board state, metadata, stats, and hint policy.
- Invalid or legacy saves fail with clear, user-visible errors.
- Import/export works for the supported puzzle types without data loss.
- Persistence and migration logic remain covered by regression tests.

**Relevant files**
- `src/richards_sudoku/persistence/persistence.py`
- `src/richards_sudoku/model/types.py`
- `tests/test_persistence.py`
- `src/richards_sudoku/main.py`

---

## Phase 4 — Extended Variant Delivery and Release Polish

### Issue 6: Implement the Extended Variant set and final app polish
**Goal:** Deliver Codewords, KenKen, and Kakuro while keeping the architecture extensible and stable.

**Scope**
- Extend the enum and registry for codewords, KenKen, and Kakuro
- Add variant-aware candidate filtering, validation, and rendering assumptions
- Support puzzle generation and solving where appropriate
- Finalize usability, accessibility, and release-quality documentation

**Acceptance criteria**
- Each extended variant is playable via the game flow with consistent controls.
- Candidate logic, rendering, and conflict behavior match the variant rules.
- The app remains stable under cross-platform execution and full CI checks.
- Release notes and engineering docs reflect the status honestly.

**Relevant files**
- `src/richards_sudoku/model/types.py`
- `src/richards_sudoku/services/candidates.py`
- `src/richards_sudoku/ui/grid_widget.py`
- `README.md`
- `milestone_roadmap.md`

---

## Suggested order of execution
1. Issue 1 — Core app baseline
2. Issue 2 — Gameplay assistance
3. Issue 3 — Variant engine / generator expansion
4. Issue 4 — Difficulty system and SE scoring
5. Issue 5 — Persistence and import/export hardening
6. Issue 6 — Extended variants and release polish

This order reflects the repository’s actual progression from playable standard Sudoku toward Beta variants, difficulty grading, and broader release readiness.
