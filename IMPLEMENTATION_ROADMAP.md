# Implementation roadmap

Current stage: pre-alpha under [alpha.md](alpha.md). Workflow fixes are implemented;
independent developer handoff and manual acceptance remain. See
[PROJECT_STATUS.md](PROJECT_STATUS.md) and [IMPLEMENTATION_ISSUES.md](IMPLEMENTATION_ISSUES.md).

| Phase | Current implementation | Remaining work |
| --- | --- | --- |
| 0 — UX/accessibility | Keyboard entry, labels/tooltips, Save/Discard/Cancel safeguards | DOC-06 fonts, contextual help, manual accessibility |
| 1 — Core | Gameplay, hints, notes, undo/redo, timer, save/resume/restart | Independent/manual workflow assessment |
| 2 — Additional variants | Jigsaw, Str8ts, Killer, SE grading; generation repairs tested | Layout variety and difficulty calibration |
| 3 — Persistence/exchange | JSON v2, backups, original clues, hypotheses, UI text/JSON exchange | Manual platform recovery checks |
| 4 — Extended variants | 1–25 input, Codewords hypotheses, KenKen/Kakuro lifecycle | Representative manual sessions |
| Alpha handoff | Written setup, tests, architecture and local install evidence | DOC-09 independent takeover/stability review |
| Beta/release | Automated matrix configuration and local regression evidence | DOC-07 manual platforms, current CI/rulesets, approvals |

Follow [ROADMAP.md](ROADMAP.md) and [speckit.tasks](speckit.tasks).
