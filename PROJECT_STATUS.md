# Project status

## Development stage

**Pre-alpha — independent Alpha handoff and review are still pending.**
Workflow fixes implemented on 2026-10-01 against the working tree based on `2149d7d`.
The package remains **0.1.0**. [alpha.md](alpha.md) defines the maturity criteria;
[TESTING.md](TESTING.md#latest-local-validation) records the actual verification.

## Alpha readiness

- [x] **A1 — Core purpose:** automated scenarios cover generation, input,
  save/resume, completion, and restart for all eight enabled variants, including
  KenKen 4×4/6×6/9×9 and 25×25. Representative desktop sessions remain DOC-07 work.
- [ ] **A2 — Stable architecture:** modules, configuration, storage, and extension
  decisions are documented; the independent architecture review is pending (DOC-09).
- [x] **A3 — Connected features:** DOC-01–05 and the generated-puzzle handoff
  (DOC-10) have implementation and regression evidence. See the scope limits below.
- [ ] **A4 — Developer handoff:** another developer must complete the documented
  clone/build/run/test/change exercise without author assistance (DOC-09).
- [x] **A5 — Understood data risks:** restore behavior, backups, atomic-save failure,
  and Save/Discard/Cancel transitions have regression checks. Known persistence
  limits and recovery instructions are documented in USER_GUIDE.md and MIGRATIONS.md.
- [x] **A6 — Documentation exists:** setup, architecture, roadmap, tests, scope,
  and limitations are maintained through [DOCUMENTATION.md](DOCUMENTATION.md).
- [x] **A7 — Major-workflow testing:** the existing suite plus
  `tests/test_alpha_workflows.py` covers the repaired flows and variant lifecycle.
  Headless tests do not replace independent or manual platform assessment.

**Beta:** pending Alpha and reliable ordinary-user evidence. **Release:** pending
candidate-specific platform validation and publication approvals. Historical batch
names, package versions, and this implementation pass do not certify those gates.

## Baseline

| Item | Current state |
| --- | --- |
| Product / package | Sudoku-inator / `sudoku-inator`; Python module `sudoku_inator` |
| Runtime | Python >=3.13, PyQt6 >=6.10 |
| Launch | `sudoku-inator` |
| Save schema | Writes version 2; reads versions 1 and 2; compatible optional fields documented in MIGRATIONS.md |
| CI | Python 3.13; configured Linux, Windows, macOS jobs; current remote evidence still pending |
| Local evidence | See TESTING.md for dated checks, installed-wheel smoke test, and limitations |

## Implementation issues

| ID | Status | Outcome / remaining work |
| --- | --- | --- |
| DOC-01 | Implemented and tested | UI JSON/text import/export, errors, and variant-aware Check Board |
| DOC-02 | Implemented and tested | Auto, Reveal, Eliminate, Naked Single, Candidate; unknown modes refused; elimination persists until a value edit recomputes candidates |
| DOC-03 | Implemented and tested | Restore remaining allowance and saved notes; original puzzle persisted for Restart; history remains session-local; failed saves preserve timer state |
| DOC-04 | Implemented and tested | F4 / Enter Value supports 1–25, pencil marks, deletion, undo/redo, and completion |
| DOC-05 | Implemented and tested | Only given Codewords mappings revealed; hypotheses editable, distinct, undoable, and saved |
| DOC-06 | Partially complete | Unsaved-progress confirmations tested; font controls, tutorial/context help, and manual accessibility review remain |
| DOC-07 | Partially complete | Automated variant lifecycle and local installation checks; manual desktop/platform sessions, current remote CI/ruleset evidence, and approvals remain |
| DOC-08 | Implemented and tested | Class-scoped fixture uses static methods; deprecation warnings removed |
| DOC-09 | Open | Independent developer handoff and architecture stability review |
| DOC-10 | Implemented and tested | Preserve worker-generated puzzle/solution; valid Str8ts layouts, distinct Killer cages, and bounded variant uniqueness checks |

## Scope and known limits

- Hints use the five existing modes. Multi-reveal and technique walkthroughs are
  future scope. Candidate is advisory and free; successful other modes spend one
  hint per invocation. Revealed values stay fixed. Undo never refunds hints.
- Text exchange carries puzzle values/rules, not a saved solution, player notes,
  hypotheses, or history. Text imports treat values as clues and cannot provide
  solution-based hints. JSON exchange preserves full session information.
- JSON restores notes exactly. A subsequent value edit recomputes board candidates;
  candidate-only edits and their undo/redo do not. History and UI preferences are
  not persisted. Legacy saves without original clues restart from their fixed cells.
- Codewords hypotheses are player notes, kept separate from the hidden solution
  mapping. Grid entry remains numeric and rendering uses letters.
- Str8ts uses cyclic consecutive layouts with black wrap boundaries and visible
  black digits. Layout variety and calibrated difficulty remain future work.
  Killer, KenKen, and Kakuro may retain extra given digits when a bounded search
  cannot prove that further clue removal preserves uniqueness.
- Eight-variant headless lifecycle checks use representative fixtures/seeds; they
  do not establish reliable ordinary-user play across all generated puzzles.

## Evidence boundaries

Local tests do not verify current remote CI, branch protection, publication, manual
cross-platform usability, or an independent developer's ability to take over.
Keep those gates open until their own evidence is recorded.
