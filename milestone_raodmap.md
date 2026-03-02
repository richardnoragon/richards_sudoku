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
  - Add extended 1–25 Sudoku.
  - Architecture supports future variants.

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

## 🌟 Full Release
**Goal:** Deliver a polished, extensible product with advanced features and scalability.

- **Advanced Features**
  - Puzzle editor (custom rule sets).
  - Online puzzle sharing & leaderboards.
  - Multiplayer timed challenges.
  - Cloud save integration.

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