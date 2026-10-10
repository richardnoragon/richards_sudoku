# CI enforcement plan

## Alpha alignment

Passing the jobs below supplies part of the [Alpha evidence](alpha.md). CI does
not certify independent developer handoff, architecture stability, or ordinary-user
reliability. Record those checks separately before changing the development stage.

The executable source is [quality-gates.yml](.github/workflows/quality-gates.yml).
This document maps the current workflow to the [constitution](speckit.constitution)
and [appendices](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md).

## Implemented checks

| Required job name | What it checks | Boundary |
| --- | --- | --- |
| Markdown Lint | All Markdown using the repository lint config | Several formatting rules disabled; no link or fact checking |
| Python Lint and Type | `ruff check src` and `mypy` | Ruff E9/F63/F7/F82; mypy covers the model package |
| Tests (ubuntu-latest) | Full pytest suite, Python 3.13, offscreen Qt with xvfb | Automated behavior and existing timing assertions |
| Tests (windows-latest) | Full pytest suite, Python 3.13, offscreen Qt | Same suite |
| Tests (macos-latest) | Full pytest suite, Python 3.13, offscreen Qt | Same suite |

## Repository settings

Require pull requests and these five checks on `main` in GitHub branch protection
or rulesets. The workflow itself does not configure repository settings.
Historical links are retained in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md);
verify the settings and job results for each release candidate.

## Manual and future enforcement

The workflow does not enforce changelog/version increments, maintainer approvals,
full accessibility, type coverage outside the model, import sorting, memory limits,
or comparison with a historical performance baseline. Review these requirements
through the release checklist. Additional automation is future work.

Governance authority is described in [GOVERNANCE.md](GOVERNANCE.md); responsible
roles are in [MAINTAINERS.md](MAINTAINERS.md). Current local evidence and commands
are in [TESTING.md](TESTING.md).
