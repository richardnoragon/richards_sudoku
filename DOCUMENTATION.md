# Documentation index and maintenance

## Development maturity authority

[alpha.md](alpha.md) defines Alpha and later-stage terminology;
[PROJECT_STATUS.md](PROJECT_STATUS.md#alpha-readiness) records the assessment and
seven-item checklist. Updated on **2026-10-01**: workflow fixes are implemented
and tested; **pre-alpha** remains pending independent handoff and review. Beta and
release need their separate manual/platform evidence. Runtime evidence is dated in TESTING.md.

Use this order: Alpha standard for maturity, project status for evidence, current
requirements for intended scope, code/tests for behavior, and release checklist for
publication. Historical “Beta”/“Post-Beta” batch labels and archived discussions do
not establish a maturity stage. Templates request evidence and do not supply it.
Update the standard, scope, status, task ledger, and affected guidance together
when changing the milestone; preserve historical source attribution and test dates.

Reviewed on 2026-09-29 against the repository code, configuration, and local checks.

## Which document answers which question?

- **What works now?** [PROJECT_STATUS.md](PROJECT_STATUS.md), then [USER_GUIDE.md](USER_GUIDE.md).
- **What remains?** [speckit.tasks](speckit.tasks), [implementation issues](IMPLEMENTATION_ISSUES.md), and [ROADMAP.md](ROADMAP.md).
- **What is required?** The constitution, appendices, PRD, and UX spec define acceptance goals.
- **What was verified?** [TESTING.md](TESTING.md) records dated local evidence; [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) controls release approval.
- **Which format/API is current?** Source code and tests establish runtime behavior; [ARCHITECTURE.md](ARCHITECTURE.md), [MIGRATIONS.md](MIGRATIONS.md), and current variant notes describe it.

If requirements and code differ, record the gap rather than claiming completion.
The current-contract sections supersede original design rounds in `speckit.specify`
and `speckit.plan`; the open-task section supersedes historical batch completion claims.
Archived discussions and source clippings are research history. Their examples and
external links are preserved snapshots, not maintained instructions or live-source verification.

Rebranding and migration: [REBRANDING.md](REBRANDING.md).

## Project document inventory

| Document | Role |
| --- | --- |
| [alpha.md](alpha.md) | Development maturity definitions, seven Alpha criteria, and current Alpha scope |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Current modules, ownership, APIs, and extension boundaries |
| [C.L.E.A.R. Lifecycle Table per Appendix.md](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md) | Required review roles and cadence |
| [CHANGELOG.md](CHANGELOG.md) | Change history; development baseline distinguished from publication |
| [CI Enforcement Plan.md](CI%20Enforcement%20Plan.md) | Actual automated checks and manual enforcement boundaries |
| [codewords_sudoku_en.md](codewords_sudoku_en.md) | Current Codewords behavior and text format |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributor setup and review workflow |
| [DECISIONS.md](DECISIONS.md) | Architecture rationale and direction |
| [DOCUMENTATION.md](DOCUMENTATION.md) | Document index, precedence, and maintenance workflow |
| [GOVERNANCE.md](GOVERNANCE.md) | Governance lifecycle and decision authority |
| [IMPLEMENTATION_ISSUES.md](IMPLEMENTATION_ISSUES.md) | Open DOC issues and acceptance evidence |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Delivery phase mapping and remaining work |
| [jigsaw_sudoku.md](jigsaw_sudoku.md) | Archived design discussion; original snippets preserved, not current APIs |
| [kakuro_sudoku.md](kakuro_sudoku.md) | Current Kakuro implementation and serialized format |
| [Kakuro_Wikipedia_en.md](Kakuro_Wikipedia_en.md) | Archived external reference snapshot; attribution and content preserved |
| [Ken Ken_Wikipedia_de.md](Ken%20Ken_Wikipedia_de.md) | Archived external reference snapshot; attribution and content preserved |
| [kenken_sudoku.md](kenken_sudoku.md) | Current KenKen implementation and serialized format |
| [killer_sudoku.md](killer_sudoku.md) | Archived design discussion; original snippets preserved, not current APIs |
| [Killer_sudoku_Wikipedia_en.md](Killer_sudoku_Wikipedia_en.md) | Archived external reference snapshot; attribution and content preserved |
| [MAINTAINERS.md](MAINTAINERS.md) | Role responsibilities; no invented assignments or approvals |
| [MIGRATIONS.md](MIGRATIONS.md) | Implemented save format and compatibility history |
| [milestone_roadmap.md](milestone_roadmap.md) | Milestone summary |
| [prd.md](prd.md) | Product requirements, with implementation status linked |
| [prd_checklist.md](prd_checklist.md) | Acceptance criteria; not a completed validation record |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Canonical current implementation snapshot and DOC issue IDs |
| [README.md](README.md) | Entry point, installation, and navigation |
| [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) | Unfinished release gate; historical links clearly labeled |
| [RELEASE_PROCESS.md](RELEASE_PROCESS.md) | Release procedure and approval requirements |
| [sudoku-inator — FULL‑SYSTEM BETA TEST PACKAGE.md](sudoku-inator%20%E2%80%94%20FULL%E2%80%91SYSTEM%20BETA%20TEST%20PACKAGE.md) | Manual acceptance template; current project branding |
| [ROADMAP.md](ROADMAP.md) | Current priorities and future scope |
| [SECURITY.md](SECURITY.md) | Reporting and local data handling policy |
| [solver.md](solver.md) | Archived design discussion; original snippets preserved, not current APIs |
| [speckit.constitution](speckit.constitution) | Project principles and normative appendix links |
| [speckit.constitution.appendix.a.md](speckit.constitution.appendix.a.md) | Code-quality contracts and serialization discipline |
| [speckit.constitution.appendix.b.md](speckit.constitution.appendix.b.md) | Required test coverage |
| [speckit.constitution.appendix.c.md](speckit.constitution.appendix.c.md) | Required UX and accessibility |
| [speckit.constitution.appendix.d.md](speckit.constitution.appendix.d.md) | Performance targets and actual enforcement |
| [speckit.constitution.appendix.e.md](speckit.constitution.appendix.e.md) | Current save schema and compatibility policy |
| [speckit.plan](speckit.plan) | Current contract links plus retained historical plan |
| [speckit.specify](speckit.specify) | Current corrections plus retained historical design rounds |
| [speckit.tasks](speckit.tasks) | Authoritative open tasks plus annotated original delivery ledger |
| [Str8ts_ Wikipedia_en.md](Str8ts_%20Wikipedia_en.md) | Archived external reference snapshot; attribution and content preserved |
| [Str8ts_Logo_250px-de.svg (1).md](Str8ts_Logo_250px-de.svg%20%281%29.md) | Archived external reference snapshot; attribution and content preserved |
| [Str8ts_Logo_250px-de.svg (2).md](Str8ts_Logo_250px-de.svg%20%282%29.md) | Archived external reference snapshot; attribution and content preserved |
| [Str8ts_Wikipedia_de.md](Str8ts_Wikipedia_de.md) | Archived external reference snapshot; attribution and content preserved |
| [SukakuExplainer.md](SukakuExplainer.md) | Archived design discussion; original snippets preserved, not current APIs |
| [TESTING.md](TESTING.md) | Canonical local validation evidence, commands, and coverage boundaries |
| [USER_GUIDE.md](USER_GUIDE.md) | Implemented user controls and limitations |
| [UX_DESIGN_SPEC.md](UX_DESIGN_SPEC.md) | Target UX; incomplete requirements explicitly identified |
| [Versioning  Enforcement Checklist.md](Versioning%20%20Enforcement%20Checklist.md) | Reusable adoption checklist; not completed evidence |
| [Versioning  Governance Review Template.md](Versioning%20%20Governance%20Review%20Template.md) | Reusable governance review template |
| [Versioning  Standard  Policy.md](Versioning%20%20Standard%20%20Policy.md) | Application, schema, and governance version policy |
| [Versioning Migration Plan Template.md](Versioning%20Migration%20Plan%20Template.md) | Reusable policy migration template |
| [Versioning Rollout Plan Template.md](Versioning%20Rollout%20Plan%20Template.md) | Reusable rollout template |

## Tooling and supporting files

- [.specify/memory/constitution.md](.specify/memory/constitution.md) is the tooling
  constitution, aligned with the root principles and current status.
- [.github/pull_request_template.md](.github/pull_request_template.md) requests review evidence.
- `.github/skills/`, `.specify/templates/`, and `.specify/extensions/` contain reusable
  tooling instructions/templates. `.kilo/` contains local tool configuration. These
  are not product delivery status records and were not rewritten as application docs.
- `_gen_templates_log.txt`, `_gen_templates_err.txt`, and `_templates_output.json`
  are generated development artifacts; screenshots and puzzle images are reference assets.

## Keeping the documents aligned

1. Check code, tests, `pyproject.toml`, and the workflow before changing behavior claims.
2. Update PROJECT_STATUS.md and affected user/API/schema guidance together.
3. Keep open task IDs and acceptance criteria consistent across task/issue/roadmap files.
4. Store exact local test results in TESTING.md with date, environment, and revision.
   Link to that evidence elsewhere rather than copying timings into every document.
5. Record changes under Unreleased; use MIGRATIONS.md for format changes.
6. Run Markdown lint and check local links. Complete release checks only with evidence
   for the release commit; retain historical evidence with its scope clearly labeled.
