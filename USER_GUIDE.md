# User Guide

This guide explains how to install, configure, and use Sudoku-inator for day-to-day puzzle play and project use.

## Current status

This guide reflects the current repository state as of the latest validated release baseline. The app supports the implemented puzzle variants and gameplay flow described in the project docs, and the current validation run remains green for the project’s checked-in test suite.

## Installation

### Requirements

- Python 3.13 or later
- A supported desktop environment
- PyQt6 dependency managed through the project package metadata

### Install from source

From the project root:

```bash
python3 -m pip install -e .
```

This installs the package in editable mode and makes the application entry points available in the current environment.

### Launch the application

After installation, start the app using:

```bash
sudoku-inator
```

You can also use the compatibility entry point:

```bash
richards-sudoku
```

## Importing

You may need to import a saved game, custom puzzle file, or variant data depending on the workflow.

### Importing a game save

1. Open the application.
2. Navigate to the import or load action in the app menu or toolbar.
3. Select the saved game file.
4. Confirm that the state is loaded correctly before continuing play.

### Importing custom content

If importing custom puzzle files or data sets:

- ensure the file format matches the application’s expected schema,
- check the file is not corrupted,
- and validate the data before trusting it as a playable game.

For best results, use files created by the application or exported from a trusted source.

## Managing content

The project supports a number of content workflows that should be handled carefully to maintain a clean and reliable game state.

### Saving progress

Use the Save action to preserve the current game state. Save files should be stored in a predictable location so they can be organized and restored later.

### Creating a new game

From the main UI, choose the relevant puzzle variant and start a fresh board. Verify that the board is generated correctly and that the status indicators reflect the current activity.

### Managing game history

The app may provide support for:

- undoing recent moves,
- redoing actions,
- reviewing move history,
- and returning to a previous game state.

Use these tools when experimenting with puzzle strategies or correcting accidental input.

### Handling variants

Sudoku-inator supports multiple puzzle variants. Before starting a new game, select the appropriate variant and confirm the board and rule set match the intended mode.

## Common workflows

### New puzzle workflow

1. Launch the application.
2. Open the puzzle menu or start-game flow.
3. Choose a variant.
4. Start a new board.
5. Play, save progress, and continue as needed.

### Resume workflow

1. Open the application.
2. Load the saved game.
3. Confirm the puzzle state matches the last saved point.
4. Continue from the current board.

### Replay or recovery workflow

If a previous action needs to be corrected:

- use undo/redo controls,
- or restore from a known backup file.

This is the safest route when the current state is uncertain or a mistake has created a broken board state.

### Trial or testing workflow

When validating new content or gameplay behavior:

- start with a small known-good puzzle,
- test one workflow at a time,
- verify the result before moving to broader validation,
- and keep a backup of progress in case the state becomes invalid.

## Backup/restore

Protecting saved progress is important, especially with longer games or custom content.

### Recommended backup practices

- keep a copy of important save files in a separate folder,
- store backups outside the active working directory whenever possible,
- keep at least one recent backup before major changes,
- and verify the backup can be loaded successfully.

### Restoring a backup

1. Locate the backup file.
2. Open the load or restore action in the app.
3. Select the backup copy.
4. Confirm the restored state matches the expected saved progress.

### Backup after major events

Back up after:

- completing a difficult puzzle,
- switching variants,
- updating or reimporting custom content,
- or making a major state change in the application.

## Troubleshooting

If a saved file does not load correctly:

- verify the file format is valid,
- confirm the file was not corrupted,
- try a more recent backup,
- and avoid importing files from untrusted or modified sources.

If the app does not launch:

- confirm Python and dependencies are installed,
- verify the project is installed in the active environment,
- and restart the terminal if required.

## Summary

Sudoku-inator is designed to support repeatable game workflows with local persistence, variant selection, and straightforward recovery. Regular save practices and backups reduce the risk of losing progress and help keep day-to-day use reliable.
