# User guide

## Alpha alignment

This is a **pre-alpha** build for developers and technical testers. The
[Alpha standard](alpha.md) is not yet met; consult the known gaps below before
relying on a workflow. Independent usability evidence remains open.

This guide describes the current desktop app. See [project status](PROJECT_STATUS.md)
for the full implementation snapshot and remaining release work.

## Install and launch

Follow [the README setup](README.md#install-and-run), using Python 3.13+ and PyQt6 >=6.10.
Run `sudoku-inator`.
The app starts with a Standard puzzle.

## Start a game

Choose **File → New Game** (`Ctrl+N`). Select a variant and Easy, Medium, Hard,
or Expert difficulty. Set the hint limit (default 3), or select Unlimited.
KenKen offers sizes 4, 6, and 9; other variants have fixed sizes.
Complex variants show generation progress and allow cancellation.
The displayed SE grade is computed separately from the chosen generation difficulty.

## Controls

| Action | Control |
| --- | --- |
| Select a cell | Click, arrow keys, Tab / Shift+Tab |
| Enter a value | Digit keys 1–9; F4 / Enter Value for the full range |
| Clear an editable cell | Backspace, Delete, or 0 |
| Toggle pencil mode | P or Edit → Pencil Mode |
| Undo / redo board edits | Ctrl+Z / Ctrl+Y |
| Apply selected hint | H |
| Save / Save As | Ctrl+S / Ctrl+Shift+S |
| Open saved game | Ctrl+O |
| Restart, keeping elapsed time | F9 |
| Restart and reset timer | Shift+F9 |
| Toggle light/dark theme | F2 |

Fixed clues, hint-filled cells, and black cells cannot be edited. Conflicts are
highlighted continuously; **Game → Check Board (F5)** reports variant-aware conflicts
or completion. **Edit → Enter Value (F4)** accepts the full symbol range, including
10–25, in normal and pencil modes. Codewords displays letters while accepting digits.

## Hints

Select a mode in the status bar, then press H:

- **Auto:** fill a random empty cell from the saved solution.
- **Reveal:** fill the selected empty cell; without a selection, use Auto.
- **Elim.:** remove one wrong candidate in the selected cell; undo/redo preserves
  the removal. A later value edit recomputes board candidates.
- **Naked:** fill cells with one computed legal candidate during a board scan.
- **Candidate:** reveal the selected cell's solution candidate without filling
  the cell or spending allowance. This is an advisory solution reveal.

Successful Auto/Reveal/Elim./Naked invocations each spend one hint. Filled cells
become fixed and cannot be undone; obsolete history for that cell is removed.
Undo never refunds hints. Candidate-only edits can be undone/redone.
Unknown modes are refused. Multi-reveal and technique walkthroughs remain future work.
Text imports have no stored solution, so solution-based hints are unavailable;
JSON session import preserves a saved solution when one exists.

## Save, resume, and recover

**File → Save / Save As** writes JSON without changing whether the timer is running.
**Open** restores board values, exact saved notes, Codewords hypotheses, timer,
stats, variant metadata, grade, and remaining hints (limit minus hints used).
Original puzzle clues are saved for Restart. Loading clears undo/redo history;
UI preferences are not persisted. A value edit recomputes candidates; saved and
candidate-only edits are preserved until then. Legacy saves without original clues
restart from their saved fixed cells, including old revealed hints.

New Game, Open, Import, Restart, and Quit/Close offer **Save / Discard / Cancel**
when board edits, notes, hypotheses, or counters have changed. Cancel, cancelled
Save As, and failed saves keep the current session. Elapsed time alone does not
mark a session dirty. Restart resets moves/hints; F9 keeps elapsed time and
Shift+F9 resets it. Save first if you want to retain the completed session.

Overwriting creates `<filename>.bak`; writes replace the destination atomically.
To recover, choose All files in Open and select the backup, then Save As to a new
JSON file. Only the previous save is retained. See [MIGRATIONS.md](MIGRATIONS.md).

## Import/export and Codewords

**Import Puzzle** accepts JSON sessions or the project text format. **Export Puzzle**
writes text or JSON. Text treats all supplied values as clues and omits session
notes, hypotheses, history, and solutions; use JSON to share/resume a session.
Exports do not change the active Save destination or mark progress as saved.
Invalid imports leave the current board intact and display an error. Puzzle-pack
APIs remain developer-only; there is no puzzle-library UI.

Codewords reveals only the given mappings, which are bold and locked. Unknown
slots start blank and accept distinct digits 1–9 as player hypotheses. Clear a
slot to remove a hypothesis. These notes have undo/redo and JSON persistence;
they do not change the hidden solution mapping or the board completion rule.

## Generation limitations

Str8ts currently uses cyclic consecutive layouts with visible black digits;
layout variety and difficulty calibration remain limited. Killer, KenKen, and
Kakuro may include extra given digits: clue removal keeps a clue whenever a bounded
search cannot prove uniqueness. Generation levels remain heuristic.

## Troubleshooting

- If launch fails, check the active Python environment and reinstall the project there.
- On Linux, a missing `libEGL.so.1` requires the operating system's Qt/EGL runtime package;
  CI installs `libegl1` on Ubuntu.
- Use the offscreen Qt setting for tests; use a normal desktop session to play.
- If a save cannot load, try a backup. Saves from newer schema versions are rejected.
- Report reproducible problems with the variant, difficulty, steps, and error message.
