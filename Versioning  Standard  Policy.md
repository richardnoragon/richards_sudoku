# Versioning policy

## Alpha alignment

[alpha.md](alpha.md) defines maturity independently of version syntax. Current
version 0.1.0 remains unchanged; the documented stage is pre-alpha. Assign an Alpha
or Beta label only after the corresponding evidence is recorded in project status.

## Application version

Sudoku-inator uses `MAJOR.MINOR.PATCH` application versions in `pyproject.toml`.
The current value is 0.1.0. Document incompatible changes, compatible features,
and fixes in [CHANGELOG.md](CHANGELOG.md), with commit/PR references in release evidence.
Do not infer a published release from package metadata or a dated changelog entry.

For Python package prereleases use Python-compatible forms such as `0.2.0a1`,
`0.2.0b1`, or `0.2.0rc1`. Keep artifact metadata and release tags consistent with
the selected package version. A `v` prefix may be used for Git tags.

## Save schema and governance versions

The save schema is a separate integer, currently `version: 2`. Compatible optional
fields with defaults may retain it; incompatible changes require migration planning.
[Appendix E](speckit.constitution.appendix.e.md) and [MIGRATIONS.md](MIGRATIONS.md)
define the format and migration history.

Constitution revisions have their own governance version. A document's template
revision is not an application release number.

## Release enforcement

Follow [RELEASE_PROCESS.md](RELEASE_PROCESS.md) and complete
[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). Version/changelog checks are currently
manual: the workflow runs Markdown lint, limited Python lint/type checks, and tests.
See [CI Enforcement Plan.md](CI%20Enforcement%20Plan.md).

Review this policy annually and when changing packaging or persistence. Record
policy amendments through the governance lifecycle. The migration, rollout, and
review templates support this process; unfilled templates are not completed evidence.

## Scope

This policy applies to the desktop package and its save files. API endpoint and
container tagging requirements become applicable only if those artifacts are introduced.
