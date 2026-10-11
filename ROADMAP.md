# Roadmap

Current implementation and evidence: [PROJECT_STATUS.md](PROJECT_STATUS.md).
The package is version 0.1.0 and the development stage is **pre-alpha**.
The next milestone is [Alpha](alpha.md): working primary workflows, stable
architecture, and an independently demonstrated developer handoff.

## Next: finish Alpha evidence

1. **DOC-09:** have another developer complete the clone/build/run/test/change
   handoff and record an architecture stability review.
2. **DOC-07:** record representative desktop sessions, including large-board
   input, Codewords, hints, data recovery, and cancellation on target platforms.
3. Review [all seven criteria](PROJECT_STATUS.md#alpha-readiness) before promotion.

## Implemented in the Alpha workflow pass

- **DOC-01–05:** UI exchange/check, supported hints, session restore, 1–25 entry,
  and editable/persisted Codewords hypotheses.
- **DOC-06 safeguards:** Save/Discard/Cancel before destructive transitions.
- **DOC-08:** fixture deprecation cleanup.
- **DOC-10:** generated-puzzle handoff and variant generation/validation repairs.

Evidence and residual limits are in [TESTING.md](TESTING.md) and
[IMPLEMENTATION_ISSUES.md](IMPLEMENTATION_ISSUES.md).

## After Alpha: Beta and publication

- Finish remaining accessibility/onboarding work (DOC-06).
- Demonstrate reliable ordinary-user workflows on supported platforms (DOC-07).
- Refresh CI and branch-protection evidence and complete release approvals.
- Improve Str8ts layout variety and calibrate difficulty against a reviewed corpus.

## Delivered foundations

- Phase 0: selection/status feedback, keyboard guidance, tooltips, accessibility labels.
- Phase 1: Standard gameplay, pencil marks, undo/redo, timing, JSON save/load.
- Phase 2: Jigsaw, Str8ts, Killer, and SE grading including advanced techniques.
- Phase 3: persistence validation, backups, and text exchange APIs.
- Phase 4: 1–25, Codewords, KenKen, and Kakuro generation/model/rendering support.

These phases do not imply all acceptance requirements or release gates are complete.
See [milestone overview](milestone_roadmap.md) and
[delivery plan](IMPLEMENTATION_ROADMAP.md).

## Later improvements

- Calibrate difficulty labels with a reviewed variant corpus.
- Expand malformed-input and variant scenario coverage.
- Add onboarding, contextual variant help, font controls, and palette customization.
- Build a puzzle library UI around the existing puzzle-pack APIs.
- Improve large-grid performance and reduce duplicated variant rules across layers.

## Future product scope

Puzzle editing, online sharing, leaderboards, multiplayer, cloud saves, and mobile
adaptation are unimplemented proposals. Define requirements and acceptance tests
before scheduling them. [UX_DESIGN_SPEC.md](UX_DESIGN_SPEC.md) describes design goals.
