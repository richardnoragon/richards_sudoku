# Milestone Roadmap: richards_sudoku

## 🎯 MVP (Minimum Viable Product)
**Goal:** Establish a working UI with basic gameplay.

- **UI Foundations**
  - Grid rendering (9x9 standard Sudoku).
  - Cell selection, number entry (keyboard/mouse).
  - Highlighting of selected cell, row, column, and region.
  - Basic themes (light/dark mode).

- **Game Basics**
  - New puzzle generation (standard Sudoku only).
  - Puzzle validation (ensure solvable).
  - Save/load functionality (JSON format).
  - Timer tracking solution duration.

- **Assistance Features**
  - Pencil marks (candidate numbers).
  - Undo/redo moves.

- **Acceptance Criteria**
  - User can start, play, and finish a standard Sudoku game.
  - UI is intuitive and responsive.
  - Save/load works reliably with puzzle state preserved.

---

## 🚀 Beta Release
**Goal:** Expand functionality and introduce multiple variants + advanced assistance.

- **Variants**
  - Add Jigsaw Sudoku.
  - Add Str8ts.
  - Add Killer Sudoku (cage‑sum constraints; `KILLER` variant in model).
  - Add extended 1–25 Sudoku.
  - Architecture supports future variants.

- **Difficulty & Grading**
  - SE difficulty rating engine (`difficulty_se.py`): 17 techniques, weighted‑average score, Easy/Medium/Hard/Extreme labels.
  - SE score displayed in status bar on new game and load.
  - SE score/label persisted in save JSON (schema v2) and restored on load without recomputing.

- **Gameplay Assistance**
  - Hint system (show possible numbers for a cell).
  - Configurable hint limits.
  - Conflict highlighting (duplicate numbers in row/column/region).

- **Game Management**
  - Import/export puzzles (JSON/text format).
  - Difficulty levels (Easy, Medium, Hard, Expert).

- **Tracking & Analytics**
  - Track moves made.
  - Track hints used.
  - End‑of‑game statistics summary.

- **Acceptance Criteria**
  - User can play multiple Sudoku variants.
  - Assistance features work consistently across variants.
  - Import/export allows puzzle sharing.

---

## ⚙️ Extended Variants
**Goal:** Enable the four variants that were present but greyed out in Beta.

- **1–25 Sudoku**
  - 25×25 grid with 5×5 box regions; symbols 1–25.
  - `OneToTwentyFiveWorker`; auto-scaling UI; 2-digit symbol display; scrollable grid.
  - Performance budget: generation < 30 s; `grade()` < 1 s; cancel always available.

- **Codewords Sudoku**
  - 9×9 grid using letters A–I instead of digits 1–9.
  - Bijective codebook (letter → digit); difficulty-scaled `given_mappings` clues.
  - `CodewordsWorker`; Codebook Panel UI; `_CodewordsMapping` SE technique (weight 1.3).

- **KenKen (Calcudoku)**
  - N×N grid for N ∈ {4, 6, 9}; row and column uniqueness (no box regions).
  - Arithmetic cages with one of +, −, ×, ÷ and a target value.
  - `KenKenCagePartitioner`; `KenKenWorker`; `_KenKenCage` SE technique (weight 1.9).
  - Cage labels show `"12+"`, `"6×"`, `"2÷"` in topmost-leftmost cell.

- **Kakuro**
  - Crossword-style grid; black header cells carry across/down run-sum clues.
  - Run-sum and no-repeat-per-run constraints; no global row/column uniqueness.
  - `KakuroTemplateLibrary`; `KakuroFillGenerator`; `KakuroWorker`.
  - Diagonal clue labels in black cells; run-peer highlight; `_KakuroRun` SE technique (weight 2.1).

- **Acceptance Criteria**
  - All four variants playable with consistent controls and assistance features.
  - Background workers with spinner and cancel for each variant.
  - SE grading, persistence, import/export working for all four variants.
  - Existing Beta variants unaffected.

---

## 🌟 Full Release
**Goal:** Deliver a polished, extensible product with advanced features and scalability.

- **Advanced Features**
  - Puzzle editor (custom rule sets).
  - Online puzzle sharing & leaderboards.
  - Multiplayer timed challenges.
  - Cloud save integration.
  - Advanced SE techniques: XY‑Wing, XYZ‑Wing, Unique Rectangles, BUG, Forcing Chains.

- **UI Enhancements**
  - Mobile‑friendly adaptation.
  - Customizable themes and accessibility options (font sizes, color palettes).
  - Keyboard shortcuts for common actions.

- **Technical Improvements**
  - Optimized solver for large grids.
  - Modular architecture with clear documentation.
  - Automated testing suite for puzzle generation/solving.

- **Acceptance Criteria**
  - Application supports advanced variants and sharing features.
  - UI is polished, accessible, and cross‑platform.
  - Solver handles large puzzles efficiently.
  - Documentation and testing ensure maintainability.

---

👉 This roadmap ensures you start with a **playable UI (MVP)**, then expand into **variants and assistance (Beta)**, and finally deliver a **feature‑rich, scalable product (Full Release)**.  