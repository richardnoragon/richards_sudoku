# Milestone roadmap

Shared status: [PROJECT_STATUS.md](PROJECT_STATUS.md). Detailed priorities:
[ROADMAP.md](ROADMAP.md). Delivery mapping: [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md).

| Milestone | Status |
| --- | --- |
| Engineering hardening | Workflow implemented: Markdown, Ruff, model mypy, three-OS tests; refresh remote evidence for release |
| UX foundation | Initial labels, status feedback, and keyboard guidance implemented; broader accessibility open |
| MVP | Standard gameplay, hint contract, and load-state fixes covered by regression tests |
| Additional variants (historically “Beta”) | Jigsaw, Str8ts, Killer, and SE techniques implemented; no maturity claim |
| Alpha | Not reached: independent handoff and architecture review remain; workflow/data safeguards tested |
| Beta readiness | Pending Alpha and reliable ordinary-user workflow evidence |
| Persistence | JSON v2, UI text/JSON exchange, restore consistency, backups, original clues, and hypotheses implemented |
| Extended variants | All four enabled; 1–25 entry and Codewords hypotheses implemented and lifecycle tested |
| Release candidate | Local installed-wheel checks pass; pending current CI, manual platforms, and sign-offs |
| Future expansion | Editor, network sharing, multiplayer, cloud, mobile remain proposals |

## Exit criteria

Meet all seven [Alpha criteria](alpha.md) before declaring Alpha. Review the repaired
primary workflows and data safeguards, then record the DOC-09 handoff. Later Beta and
publication checks require their own evidence. Resolve DOC-01 through DOC-10 in
[IMPLEMENTATION_ISSUES.md](IMPLEMENTATION_ISSUES.md) and
[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). Maintain runtime/schema compatibility
and record any future format changes in [MIGRATIONS.md](MIGRATIONS.md).

Performance targets are maintained in [Appendix D](speckit.constitution.appendix.d.md).
Local automated results live only in [TESTING.md](TESTING.md#latest-local-validation).
