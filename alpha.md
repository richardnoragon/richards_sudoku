# Alpha standard

This document defines development maturity for Sudoku-inator. It consolidates the
original Alpha discussion into project criteria. Current evidence and unchecked
criteria are recorded in [PROJECT_STATUS.md](PROJECT_STATUS.md#alpha-readiness).

## Definition

**Alpha** is reached when the software demonstrates its intended purpose end-to-end,
its architecture is sufficiently stable, and another developer can understand,
build, run, and continue development using the repository and its documentation
without direct assistance from the original author.

Alpha is usable by developers and technically knowledgeable testers. Defects,
incomplete secondary workflows, missing polish, and some design changes are expected.
Primary workflows must work; major architectural rewrites should no longer be expected.

## Required criteria

1. **Core purpose:** the application performs its main job end-to-end.
2. **Stable architecture:** module boundaries, configuration, and storage decisions
   are documented and sufficiently settled for another developer to extend the app.
3. **Connected features:** most planned Alpha features exist and are integrated;
   primary workflows work from the user interface through persistence and recovery.
4. **Developer handoff:** a different developer can clone, install/build, launch,
   test, understand the architecture, and make a small change using written guidance.
5. **Understood data risks:** known limitations and recovery steps are documented;
   corruption and unexpected destruction of user data are no longer routine.
6. **Documentation:** README, build/run instructions, architecture overview, and
   development roadmap exist and accurately describe the checked-out software.
7. **Testing:** repeatable tests verify major workflows. Comprehensive coverage,
   performance tuning, convenience features, and visual polish may follow later.

All seven criteria need evidence before declaring Alpha. Use the checklist in
[project status](PROJECT_STATUS.md#alpha-readiness); completed implementation batches,
package versions, or passing unit tests alone do not establish the stage.

## Sudoku-inator Alpha scope

The working scope is the currently advertised desktop puzzle app: all eight enabled
variants, generation, complete value entry, pencil marks, hints, undo/redo,
completion, restart, JSON save/resume, and puzzle import/export through the UI.
Check Board must give the advertised feedback. Codewords must have an agreed,
working mapping interaction. Hint and saved-session behavior must have one tested
contract shared by the UI, code, and documentation. The Alpha hint scope is Auto,
Reveal, Eliminate, Naked Single, and Candidate; Multi-reveal and Walkthrough are
deferred. Text imports omit solutions and therefore cannot offer solution-based
hints; JSON sessions retain them. See USER_GUIDE.md for the full contract.

DOC-01 through DOC-05 and the unsaved-progress safeguards in DOC-06 define this scope
and now have implementation evidence in PROJECT_STATUS.md. DOC-10 covers the
generated-puzzle handoff and variant corrections found during lifecycle testing.
DOC-09 records the independent developer handoff and architecture review. The
fresh-install and major-workflow evidence in DOC-07 also supports Alpha; remaining
platform/release approvals belong to later readiness checks.

Font customization, tutorials, extra palettes, performance tuning, and advanced
convenience features may remain open at Alpha if basic use is viable and limitations
are explicit. Existing constitutional and publication requirements still apply.
A smaller Alpha scope requires a recorded scope decision and matching changes to
advertised capabilities, requirements, and acceptance tests; a deferral cannot make
a broken primary workflow satisfy the criterion.

## Later stages

**Beta**, from the original discussion, is reached when ordinary users can reliably
use the software for real work. Defects may remain, but data loss and workflow
failures are exceptional. Alpha evidence is a prerequisite; representative manual
sessions and platform validation must demonstrate that reliability.

**Release** is the project's publication gate: the agreed scope is validated, known
limitations and support instructions are documented, and the required approvals in
[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) are recorded. This operational definition
extends the original discussion; Alpha does not itself authorize publication.

The package version is independent of maturity. Historical “Beta” and “Post-Beta”
batch names describe delivery groups and do not certify Beta readiness.
