# Governance

## Alpha alignment

Apply [alpha.md](alpha.md) when assigning a development stage. Require linked
evidence for all seven Alpha criteria, including independent handoff (DOC-09).
Document scope changes explicitly; release exceptions cannot make an unmet Alpha
criterion complete. Publication approval remains governed by the checklist.

Sudoku-inator follows the [constitution](speckit.constitution) and its normative
appendices. The [Spec Kit constitution](.specify/memory/constitution.md) expresses
the same principles for development tooling; it does not establish a second release baseline.

## C.L.E.A.R. lifecycle

- **Codify:** document rules and requirements.
- **Legitimize:** obtain the responsible maintainer review.
- **Enforce:** apply implemented CI checks and required manual review.
- **Adopt:** include approved changes and documentation in the release.
- **Review:** revisit each appendix on its defined cadence.

The [lifecycle table](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md) defines
review roles and cadence. [MAINTAINERS.md](MAINTAINERS.md) defines responsibilities.

## Change and release decisions

Proposals should explain rationale, impact, compatibility, relevant tests, and
affected documents. Core maintainers resolve disputes using the constitution;
appendix changes require the roles specified in the lifecycle table.
Record approvals in the PR or release evidence. Editing a checklist or passing CI
does not itself grant approval.

No release proceeds until [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) is satisfied,
including recorded exceptions and corrective actions. Record schema evolution in
[MIGRATIONS.md](MIGRATIONS.md) and release changes in [CHANGELOG.md](CHANGELOG.md).

See [CI Enforcement Plan.md](CI%20Enforcement%20Plan.md) for actual automation and
[DOCUMENTATION.md](DOCUMENTATION.md) for document ownership and precedence.
