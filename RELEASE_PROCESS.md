# Release Process

This document defines the release process for Sudoku-inator and provides a consistent, repeatable path from feature completion to published release.

## Current release status

The project currently reflects a stable, verified beta/release-candidate status for the implemented feature set.

- Validation baseline: `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`
- Result: `583 passed, 2 warnings in 2.92s`
- Release posture: current roadmap items are operationally stable, with remaining work focused on product polish, future content, or optional expansion rather than core defect repair.

## Feature freeze

A feature freeze begins when the release target scope has been agreed and the release branch is created.

### Entry criteria

The feature freeze starts after:

- the release goals are documented,
- key milestones are reviewed,
- blocking issues are identified and prioritized,
- and the team agrees that no new scope should be introduced without explicit approval.

### During the freeze

- only bug fixes, stability work, and release-critical tasks are allowed,
- no unapproved new features or large refactors should land,
- work is tracked against the release milestone,
- outstanding risks are reviewed daily or at each release checkpoint.

### Exit criteria

The feature freeze ends when:

- the release branch is stable,
- acceptance tests pass,
- the release candidate is validated,
- and no release-blocking issues remain open.

## RC creation

A release candidate (RC) is created after the feature freeze begins and the codebase is considered stable enough for external validation.

### RC process

1. Create a release branch from the current stable development state.
2. Bump the version to the release-candidate tag or prerelease number.
3. Run the full validation set, including regression and smoke checks.
4. Document known limitations and explicitly tracked issues.
5. Publish the RC for trial use and feedback.

### RC requirements

The RC should be considered releasable only if:

- all critical tests pass,
- no release-blocking defects remain,
- packaging and install steps work cleanly,
- and basic gameplay flows remain functional.

## Trial periods

A trial period is used to gather real-world feedback before the final release is approved.

### Purpose

The trial period helps confirm that the release candidate behaves correctly under realistic use, including:

- startup flow
- save/load operations
- puzzle generation and validity
- variant stability
- UI responsiveness
- common user interactions

### Trial duration

The length of the trial period should be proportional to the change size and risk. For a minor release, a short focused trial may be sufficient. For a larger release, a longer validation window may be required before final approval.

### Trial feedback handling

- bugs found during the trial should be triaged by severity,
- all release-blocking issues must be resolved before final approval,
- non-blocking issues should be logged for future follow-up,
- and any accepted change after RC publication should be evaluated for its impact on release scope.

## Release approval

Release approval is a checkpoint confirming that the build is ready for publication.

### Approval criteria

A release should be approved only when:

- all required tests pass,
- regression requirements are satisfied,
- the RC trial period is complete or the remaining issues are accepted as non-blocking,
- documentation is current,
- and the release notes accurately reflect the build.

### Approval roles

Approval may be granted by the project maintainer, designated release owner, or a defined decision-maker for the repository. The process should remain explicit and consistent for every release.

### Final release action

Once approved:

- finalize the version number,
- update the changelog and release notes,
- publish the release artifact,
- and tag the repository according to the project’s versioning rules.

## Regression requirements

Regression requirements are mandatory before a release can be approved.

### Required regression coverage

The release must confirm the following areas remain stable:

- core gameplay rules
- solver and validation behavior
- persistence and save/load flows
- variant-specific logic
- UI action wiring and status behavior
- application startup and shutdown
- high-risk bug fixes from the current cycle

### Regression gate

The release is blocked if:

- a previously fixed bug reappears,
- a core rule fails under normal usage,
- save compatibility breaks,
- or a critical user workflow is no longer functional.

Any regression must be evaluated, fixed, and re-tested before the final release approval.

## Release readiness checklist

Before final publishing, confirm all of the following:

- feature freeze has started and is respected
- RC has been created and tested
- trial period has produced acceptable results
- release approval is documented
- regression requirements are satisfied
- changelog and release notes are current
- deployment or distribution instructions are complete

## Summary

The release process is designed to reduce risk and improve consistency. Feature freeze, RC validation, trial feedback, and release approval together create a disciplined path from development completion to publication while protecting the project from avoidable regressions.
