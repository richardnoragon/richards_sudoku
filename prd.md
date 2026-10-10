# Product Requirements Document (PRD): Sudoku-inator

## Alpha workflow contract (2026-10-01)

Supported hints are Auto, Reveal, Eliminate, Naked Single, and Candidate. Candidate
is free; other successful invocations spend one hint. Multi-reveal and technique
walkthroughs are future scope. Text exchange transfers clues and rules without a
solution or session notes; JSON preserves session data. History remains session-local.
Codewords hypotheses are separate player notes with undo/redo and JSON persistence.
F4 accepts the full symbol range. See USER_GUIDE.md for the current interaction contract.

## Alpha alignment

[alpha.md](alpha.md#sudoku-inator-alpha-scope) defines the current Alpha scope.
Primary advertised workflows must function end-to-end before Alpha; the broader
requirements below remain targets where implementation is incomplete. Current
stage is pre-alpha; DOC-09 also requires developer handoff and architecture review.

## Status and scope

This document states product requirements. The implemented baseline and exceptions
are recorded in [PROJECT_STATUS.md](PROJECT_STATUS.md); acceptance work is in
[prd_checklist.md](prd_checklist.md). All eight variants have automated lifecycle coverage. 1–25 entry, Codewords
hypotheses, import/export, and unsaved-progress safeguards are implemented; broader
accessibility and independent/manual assessment remain open.


## 1. Overview
A Python application that allows users to **create, solve, and share Sudoku puzzles** across multiple variants. The system supports game persistence (load/save), user assistance features (hints, pencil marks), and performance tracking (time, moves, hint usage).

---

## 2. Core Features

### 2.1 Game Management
- Load existing Sudoku games from local storage.
- Save current progress to local storage.
- Create generated puzzles. User-defined puzzle editing remains future scope.
- Import/export puzzles for sharing with others (e.g., JSON, text, or custom format).

### 2.2 Variants
- Standard 9x9 Sudoku.
- Jigsaw Sudoku (irregular regions).
- Str8ts.
- Killer Sudoku (cage‑sum constraints).
- 1–25 Sudoku (25×25 grid with symbols 1–25; Extended Variants phase).
- Codewords Sudoku (9×9; letters A–I substitute for digits 1–9; bijective codebook with difficulty-scaled given mappings; Extended Variants phase).
- KenKen / Calcudoku (N×N for N ∈ {4,6,9}; row and column uniqueness; arithmetic cages with +, −, ×, ÷ operations; Extended Variants phase).
- Kakuro (crossword-sum grid; run-sum and no-repeat-per-run constraints; diagonal clue labels in black cells; Extended Variants phase).
- Architecture supports future variants via variant registry.

### 2.3 Gameplay Assistance
- In‑game help system.
- Hint functionality:
  - Show possible numbers for a selected square.
  - Limit number of hints available per game (configurable).
- Pencil‑in notes (candidate numbers per cell).
- Highlight conflicts (duplicate numbers in row/column/region).
- Undo/redo moves.
- **Difficulty levels** (Easy, Medium, Hard, Expert) selectable at new game; SE grading uses Extreme for its highest category.
- **SE difficulty rating**: automatic grading via SukakuExplainer‑style simulation; score (0–8.0) and category displayed in status bar at game start and after load.

### 2.4 Tracking & Analytics
- Timer to measure solution duration.
- Track number of moves made.
- Track number of hints used.
- Option to enforce hint limits.
- Game statistics summary at completion.

---

## 3. User Interface

### 3.1 Display
- Grid visualization with clear cell boundaries.
- Support for multiple grid sizes (9x9, 25x25, etc.).
- Visual differentiation for pencil marks vs. confirmed entries.
- Highlighting of selected cell, row, column, and region.

### 3.2 Controls
- Mouse and/or keyboard input for number entry.
- Buttons/menus for:
  - New game
  - Load/save
  - Import/export
  - Hint request
  - Toggle pencil mode
  - Undo/redo

### 3.3 Accessibility
- Configurable color themes (light/dark mode).
- Adjustable font sizes (required; not yet exposed as a user setting).
- Keyboard shortcuts for common actions.

---

## 4. Technical Requirements

### 4.1 Architecture
- Modular Python codebase with separation of concerns:
  - Puzzle generation
  - Puzzle solving
  - UI/UX PyQt
  - Persistence (load/save/import/export)
  - Statistics tracking
- Extensible design to add new Sudoku variants.

### 4.2 Data Formats
- JSON for save files and puzzle exchange.
- Internal representation of puzzles as matrices or graph structures.

### 4.3 Solver
- Backtracking algorithm for solving.
- Optimizations for larger grids (e.g., constraint propagation).
- Validation of puzzle solvability before game start.

---

## 5. Future Enhancements
- Multiplayer or competitive mode (timed challenges).
- Online puzzle sharing and leaderboards.
- Puzzle editor for custom rule sets.
- Mobile‑friendly UI adaptation.
- Integration with cloud storage for save files.
- Further calibration of the implemented advanced SE techniques: XY-Wing, XYZ-Wing, Unique Rectangles, BUG, and Forcing Chains.

---

## 6. Non‑Functional Requirements
- **Performance:** Solver should handle large grids efficiently.
- **Maintainability:** Clear documentation and modular design for easy extension.
- **Portability:** Cross‑platform support (Windows, macOS, Linux).
- **Usability:** Intuitive interface for beginners and advanced players.
- **Reliability:** Ensure save/load integrity and prevent data loss.

---