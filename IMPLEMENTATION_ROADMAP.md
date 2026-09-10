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
- The interface is easier to understand for first-time users.
- Core actions are more discoverable and less error-prone.
- The app remains comfortable for both keyboard and mouse users.
- Accessibility and readability improve without compromising the game experience.

---

### Phase 1 — MVP Completion
**Target outcome:** A fully usable standard Sudoku app with dependable game flow.

**Primary work**
- Finish the gameplay loop: new game, solve flow, validation, save/load
- Stabilize input handling and selection logic
- Complete hint, pencil, and undo/redo behaviors
- Seal UI feedback, completion states, and restart behaviors

**Exit criteria**
- A user can play a full standard game without a broken state or save corruption.
- The app is stable under repeated new-game and session transitions.
- The core quality gates still pass reliably.

---

### Phase 2 — Beta Variant Expansion
**Target outcome:** Extend the app to the large Beta set: Jigsaw, Str8ts, Killer, and broader assistance features.

**Primary work**
- Finish generator and validation logic for each Beta variant
- Complete candidate filtering and variant-specific conflict detection
- Add thinner variant-aware rendering and cage/black-cell logic
- Make difficulty scoring and hint policies consistent across variants

**Exit criteria**
- The Beta variants are playable and visually consistent.
- Difficulty and candidate guidance reflect the underlying rules.
- The app handles cancellation, uniqueness checks, and generation retries correctly.

---

### Phase 3 — Persistence, Import/Export, and Hardening
**Target outcome:** Make the app robust in real use and safe across upgrades.

**Primary work**
- Harden persistence and migration behavior for JSON saves
- Validate variant metadata and error handling on load
- Support import/export for supported formats and board states
- Review performance and regression coverage for each supported mode

**Exit criteria**
- Save/load is deterministic and safe against corrupted or older data.
- Import/export supports practical sharing flows.
- Regression tests protect the app from schema and state drift.

---

### Phase 4 — Extended Variant Release
**Target outcome:** Add Codewords, KenKen, and Kakuro as production-ready extended variants.

**Primary work**
- Extend enums, model rules, and candidate filters for each variant
- Implement variant-specific rendering and conflict logic
- Add project-level QA for cross-variant correctness and performance
- Update release documentation and onboarding content

**Exit criteria**
- All extended variants are playable with the same core controls and assistance model.
- Variant-specific constraints are correctly reflected in both logic and UI.
- The project is ready for a broader release candidate review.

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
