<!--
Sync Impact Report
- Version change: n/a → 1.0.0
- Modified principles: n/a → I. Variant Correctness, II. Accessibility and Playability First, III. Test-First Quality Gate, IV. Release Discipline and Compatibility, V. Simplicity, Precision, and Maintainability
- Added sections: Project Constraints, Development Workflow
- Removed sections: none
- Templates requiring updates: .specify/templates/plan-template.md — ✅ reviewed for constitution-check alignment; .specify/templates/spec-template.md — ✅ reviewed for requirement and acceptance alignment; .specify/templates/tasks-template.md — ✅ reviewed for test-first and release-gate alignment
- Follow-up TODOs: none
-->

# Sudoku-inator Constitution

## Development maturity alignment

Use [the Alpha standard](../../alpha.md) and the
[readiness checklist](../../PROJECT_STATUS.md#alpha-readiness) for milestone claims.
Current stage is pre-alpha. Working primary workflows, stable architecture, and
independent developer handoff require evidence; historical batch names do not
certify Alpha or Beta. This alignment does not record ratification or publication approval.

Editorial alignment reviewed 2026-09-29: the public name is Sudoku-inator; the
Python package remains `richards_sudoku`. This tooling constitution shares the
principles in [the project constitution](../../speckit.constitution) and its appendices.
[Project status](../../PROJECT_STATUS.md) records implementation gaps; CI scope is
specified by [the enforcement plan](../../CI%20Enforcement%20Plan.md).
The ratification/version record below is unchanged by this documentation clarification.

Current naming (2026-10-10): Python package `sudoku_inator`; the earlier naming
note above is historical. See [REBRANDING.md](../../REBRANDING.md).

## Core Principles

### I. Variant Correctness
The project MUST preserve puzzle rule correctness across all supported variants: standard Sudoku, Jigsaw, Str8ts, Killer, 1to25, Codewords, KenKen, and Kakuro. Every variant's solver, generator, validator, and UI behavior MUST match the published rules before release. When a rule interpretation is ambiguous, the project MUST choose the documented canonical interpretation and record it in design notes rather than silently diverging.

### II. Accessibility and Playability First
The app MUST remain playable by keyboard and assistive technology users. Status, focus, labels, and feedback MUST be clear enough for a player to understand current state, legal moves, errors, and recovery actions without guesswork. UX changes that improve clarity, cognition, or input flow take priority over purely cosmetic refinements.

### III. Test-First Quality Gate
New behavior MUST be covered by tests before implementation is considered complete. Regression tests MUST exist for solver correctness, variant logic, persistence boundaries, and UI-critical user flows. CI MUST fail when the targeted behavior is untested or when static checks detect issues. The project MUST run the same quality gates locally prior to release: ruff check src, mypy, and pytest -q with the headless Qt configuration.

### IV. Release Discipline and Compatibility
The project MUST define and preserve a release baseline: versioned features, changelog intent, and migration notes for any persistence or behavior changes. Breaking changes to puzzle rules, save format, or user-facing workflows MUST be explicit, documented, and versioned. Releasing without validation against the current release checklist is prohibited.

### V. Simplicity, Precision, and Maintainability
The codebase MUST prefer explicit, readable implementations over cleverness. Shared contracts, model boundaries, and naming MUST be consistent across solver, persistence, and UI layers. Complexity MUST be justified by a concrete requirement; otherwise, the simpler and more testable solution wins.

## Project Constraints
The project is a Python 3.13+ desktop application built around PyQt6 and a solver-centric architecture. The repository MUST keep its current library boundaries explicit: model, services, persistence, UI, and solver responsibilities remain separate, and cross-layer coupling is not allowed unless required by a verified design need. Save and state interactions MUST remain deterministic and recoverable; user progress MUST not be lost silently. All generator, solver, and difficulty logic MUST remain reproducible under headless CI conditions.

## Development Workflow
All feature work MUST follow the Spec Kit flow: generate or update requirements, plan, and task artifacts before implementation when the change is not a trivial fix. Each task or story MUST define testable outcomes, and implementation MUST stop when validation evidence is missing. Reviews MUST confirm compliance with variant rules, accessibility requirements, release readiness, and repository quality gates before merge. Changes that affect puzzle correctness, persistence, or UX MUST include the relevant validation evidence in the review record.

## Governance
This Constitution governs all product, engineering, and release decisions for sudoku-inator. It supersedes informal practices where conflict exists. Any amendment MUST be proposed with a concrete governance reason, the updated principle or rule, and the migration or compatibility impact. Changes to rules or principles require a PR that includes the revised text, rationale, and evidence that the project remains compliant with the existing release gates.

The project MUST use semantic versioning for constitutional changes:
- MAJOR: backward-incompatible governance or rule changes;
- MINOR: new principle or material expansion of an existing rule;
- PATCH: clarifying or editorial updates that do not change behavior.

Compliance review MUST check: solver correctness, accessibility expectations, persistence safety, and CI quality-gate results. If a rule cannot be met, the team MUST document the exception, the risk, and the corrective action before merging.

**Version**: 1.0.0 | **Ratified**: 2026-09-13 | **Last Amended**: 2026-09-13
