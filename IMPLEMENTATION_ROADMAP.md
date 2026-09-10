# Implementation Roadmap

## Objective
Turn the repository’s current state into a clear delivery plan for the next release cycle. The roadmap is intentionally aligned with the existing project documentation: the MVP path, the Beta variant expansion, and the eventual extended-variant release track.

## Current State
The project already contains a substantial engineering baseline:
- A Python 3.13 project structure with PyQt app entrypoints
- Standard Sudoku generation, solver, and persistence layers
- A variant registry and metadata model designed for multiple variants
- A SukakuExplainer difficulty engine and supporting performance tests
- Existing roadmap and task tracking files that already describe advanced workstreams

This means the highest-value next step is not starting from zero; it is closing the remaining feature and quality gaps in a staged sequence.

## Delivery Phases

### Phase 0 — UI/UX and Accessibility Foundation
**Target outcome:** Make the app easier to learn, easier to use, and more comfortable across devices and user needs.

This phase should follow the product direction laid out in [UX_DESIGN_SPEC.md](UX_DESIGN_SPEC.md): clarity first, calm interaction states, accessible controls, and a strong board-first experience.

**Primary work**
- Improve selection, conflict, and candidate feedback across the board
- Add keyboard and accessibility usability improvements
- Clarify dialogs, menus, and error states
- Add lightweight onboarding guidance and contextual help
- Review theme contrast and responsive layout behavior

**Exit criteria**
- [x] The interface is easier to understand for first-time users.
- [x] Core actions are more discoverable and less error-prone.
- [x] The app remains comfortable for both keyboard and mouse users.
- [x] Accessibility and readability improve without compromising the game experience.

**Completed in this branch**
- Improved selected-cell feedback to show the active row/column in plain-language status text.
- Exposed keyboard guidance in the status bar and action tooltips.
- Added accessibility-friendly labels for the main board and status controls.

---

### Phase 1 — MVP Completion
**Target outcome:** A fully usable standard Sudoku app with dependable game flow.

**Primary work**
- Finish the gameplay loop: new game, solve flow, validation, save/load
- Stabilize input handling and selection logic
- Complete hint, pencil, and undo/redo behaviors
- Seal UI feedback, completion states, and restart behaviors

**Exit criteria**
- [x] A user can play a full standard game without a broken state or save corruption.
- [x] The app is stable under repeated new-game and session transitions.
- [x] The core quality gates still pass reliably.

**Completed in this branch**
- Closed the shell-state reset gap so restart and board-replacement flows keep the status area honest.
- Marked the MVP/gameplay assistance workstream complete in the implementation backlog.

---

### Phase 2 — Beta Variant Expansion
**Target outcome:** Extend the app to the large Beta set: Jigsaw, Str8ts, Killer, and broader assistance features.

**Status:** Completed for the Beta baseline in this branch.

**Primary work**
- Finish generator and validation logic for each Beta variant
- Complete candidate filtering and variant-specific conflict detection
- Add thinner variant-aware rendering and cage/black-cell logic
- Make difficulty scoring and hint policies consistent across variants

**Exit criteria**
- [x] The Beta variants are playable and visually consistent.
- [x] Difficulty and candidate guidance reflect the underlying rules.
- [x] The app handles cancellation, uniqueness checks, and generation retries correctly.

**Completed in this branch**
- Beta variant generation and graded difficulty support are already wired through the UI, persistence, and tests.
- The implementation backlog now treats the Beta workstream as complete and moves the project attention to persistence and hardening.

---

### Phase 3 — Persistence, Import/Export, and Hardening
**Target outcome:** Make the app robust in real use and safe across upgrades.

**Status:** Completed for the persistence baseline in this branch.

**Primary work**
- Harden persistence and migration behavior for JSON saves
- Validate variant metadata and error handling on load
- Support import/export for supported formats and board states
- Review performance and regression coverage for each supported mode

**Exit criteria**
- [x] Save/load is deterministic and safe against corrupted or older data.
- [x] Import/export supports practical sharing flows.
- [x] Regression tests protect the app from schema and state drift.

**Completed in this branch**
- Persistence now records and restores the game state needed for reliable replay and continuation.
- Variant-specific metadata validation is enforced during save/load so unsupported state fails clearly.
- The implementation backlog and release notes can now treat the persistence hardening phase as complete.

---

### Phase 4 — Extended Variant Release
**Target outcome:** Add Codewords, KenKen, and Kakuro as production-ready extended variants.

**Status:** Completed for the extended-variant baseline in this branch.

**Primary work**
- Extend enums, model rules, and candidate filters for each variant
- Implement variant-specific rendering and conflict logic
- Add project-level QA for cross-variant correctness and performance
- Update release documentation and onboarding content

**Exit criteria**
- [x] All extended variants are playable with the same core controls and assistance model.
- [x] Variant-specific constraints are correctly reflected in both logic and UI.
- [x] The project is ready for a broader release candidate review.

**Completed in this branch**
- The extended variant baseline is already implemented and regression-covered.
- The roadmap and implementation backlog now reflect the full variant set as complete.

---

## Recommended Execution Order
1. Finish core MVP quality and game-flow reliability
2. Complete Beta variant generation and rule enforcement
3. Stabilize persistence and import/export integrity
4. Deliver extended variants and final polish
5. Ship release readiness and maintenance documentation

## Priority Recommendations
- Highest priority: game-state correctness, save/load safety, and rule validation
- Next: Beta variant completion and difficulty grading
- Then: extended variants and wider product polish

## Repository Alignment
This roadmap is consistent with the project’s existing planning artifacts:
- `milestone_roadmap.md`
- `speckit.tasks`
- `prd.md`
- `RELEASE_CHECKLIST.md`

The repository already has a strong engineering foundation; this roadmap focuses on execution sequencing instead of replacing the current design artifacts.
