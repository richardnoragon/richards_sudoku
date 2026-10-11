# Implementation issues

Updated 2026-10-01. [PROJECT_STATUS.md](PROJECT_STATUS.md) records implementation
status; [alpha.md](alpha.md) defines acceptance. The project remains pre-alpha
pending DOC-09 and the remaining human validation. Historical batches are delivery
records rather than proof of current readiness.

| ID | Status | Acceptance evidence / remaining work |
| --- | --- | --- |
| DOC-01 | Implemented | Import/export actions exercise JSON and text; Check Board uses shared variant validation; error paths preserve the active session |
| DOC-02 | Implemented | Five supported modes documented; unknown modes refused; elimination survives undo/redo; Multi-reveal/Walkthrough deferred |
| DOC-03 | Implemented | Hints and notes round-trip; original puzzle survives reload/restart; session-local history documented; timer preserved on save failure |
| DOC-04 | Implemented | F4 accepts values 1–25 in normal/pencil mode; deletion, undo/redo, 25×25 completion covered |
| DOC-05 | Implemented | Given mappings locked; unknown slots blank/editable; hypotheses in board history and JSON; solution mapping unchanged |
| DOC-06 | Partial | Save/Discard/Cancel protects New/Open/Import/Restart/Close, including failed/cancelled saves; font controls, contextual help, and manual accessibility remain |
| DOC-07 | Partial | Local automated lifecycle and install evidence in TESTING.md; manual platform sessions, current CI/rulesets, and approvals remain |
| DOC-08 | Implemented | Static class-scoped performance fixtures; full suite without prior deprecation warnings |
| DOC-09 | Open | Independent developer records clone/build/run/test/change and architecture stability review using CONTRIBUTING.md |
| DOC-10 | Implemented | Shell uses generated puzzle/solution; Str8ts runs and Killer cages valid; variant clue removal requires bounded uniqueness proof |

Regression evidence: [tests/test_alpha_workflows.py](tests/test_alpha_workflows.py),
existing variant/persistence suites, and [TESTING.md](TESTING.md).

## Next actions

Complete the independent handoff and architecture review, then assess Alpha using
all seven criteria. Continue accessibility work and manual platform validation for
Beta and release. Keep known limits in USER_GUIDE.md and PROJECT_STATUS.md visible.
