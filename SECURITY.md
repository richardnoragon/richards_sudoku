# Security Policy

This document defines the security posture for Sudoku-inator and gives contributors and users a clear way to report issues and understand how the project handles local data and operational risk.

## Current project status

The project is currently in a stable beta/release-candidate state for the implemented feature set, with active local validation and a documented operational baseline. The codebase is primarily a desktop application with local save-state handling and limited remote exposure by default.

## Supported versions

The project currently supports the following runtime and packaging baseline:

- Python 3.13+
- PyQt6-compatible desktop runtime
- Current stable release branch and the most recent development branch in active maintenance

Because this project is still in active development, the project team may only provide security updates for the current release line and the most recent actively maintained development branch.

Users are encouraged to keep their environment updated to the latest supported release to receive fixes and security hardening updates.

If a security issue is reported against an older version, the maintainers may provide guidance but are not obligated to backport fixes unless explicitly agreed.

## Vulnerability reporting

If you believe you have discovered a security vulnerability in Sudoku-inator, please report it privately and responsibly.

### How to report

Please send details to the project maintainer or repository security contact through the project’s private reporting channel, GitHub Security Advisories if enabled, or another designated secure contact method used by the repository.

Include:

- a clear description of the issue
- affected version or branch
- reproduction steps or proof of concept
- impact assessment
- suggested mitigation, if known

### Reporting expectations

- Do not publicly disclose the vulnerability before a fix is available.
- Do not include sensitive data or credentials in issue reports.
- If the issue involves user-generated content, local files, or save state, provide enough detail to understand the scope without exposing sensitive material.

The maintainers will acknowledge valid reports as quickly as practical and will work toward a fix and coordinated disclosure timeline.

## Data storage

Sudoku-inator is primarily a desktop application and stores user state locally on the device running the application.

### Local storage characteristics

- puzzle state may be saved to local files
- game progress and metadata may be stored in user-accessible persistence files
- saved data should be treated as local user data, not as highly sensitive financial or personal information

### Security considerations

- Save files should be stored in a trusted local location with normal OS permissions.
- Avoid storing sensitive personal data in game saves unless explicitly required by a feature.
- If game data is exported or shared, verify the destination is trusted.
- Prefer standard file permissions and secure local directories rather than world-readable shared locations.

### Recommended handling practices

- Keep backups of game progress in a trusted, user-controlled directory.
- Validate save files before loading them, especially if they come from an untrusted source.
- Do not execute untrusted game files or scripts from external locations.

## Backup recommendations

Regular backups are recommended to reduce the risk of data loss and to support recovery from local corruption or accidental deletion.

### Best practices

- Create regular backups of saved games and custom puzzle files.
- Store backups in a separate location from the primary save directory.
- Keep at least one recent backup outside the active working directory.
- If using cloud sync, ensure the sync destination is trusted and versioned.
- Periodically verify that backup files can be restored and opened successfully.

### Operational guidance

- Back up before major version upgrades.
- Back up before resetting game state or deleting save data.
- Keep an export or manual copy of important puzzle progress, especially for long-running sessions.

## Security posture

This project is designed as a local desktop application with limited external data exposure. The main risks are therefore operational and data integrity issues rather than remote exploitation by default.

The maintainers will continue to monitor known issues, dependency updates, and release readiness. Users are expected to run supported versions and keep their local environments current.

## Scope

This policy applies to the Sudoku-inator project code, packaging, and repository-managed release assets. It does not cover third-party tools, operating systems, or external cloud providers beyond the project’s direct control.
