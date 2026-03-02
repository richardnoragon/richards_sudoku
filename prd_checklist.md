# Product Requirements Document (PRD) Checklist: richards_sudoku

## 1. Game Management

### User Story 1.1  
As a user, I want to **create a new Sudoku puzzle** so that I can start playing immediately.  
- **Acceptance Criteria:**  
  - User can select puzzle type (Standard, Jigsaw, Str8ts, 1–25).  
  - Puzzle is generated with valid solvable configuration.  
  - Difficulty level can be chosen (Easy, Medium, Hard, Expert).  

### User Story 1.2  
As a user, I want to **save my current game** so I can resume later.  
- **Acceptance Criteria:**  
  - Save file stored in JSON format.  
  - Save includes puzzle state, timer, moves, and hints used.  
  - User can name save files or use auto‑generated names.  

### User Story 1.3  
As a user, I want to **load a saved game** so I can continue where I left off.  
- **Acceptance Criteria:**  
  - Load restores puzzle state exactly as saved.  
  - Timer resumes from saved time.  
  - Pencil marks and hints are preserved.  

### User Story 1.4  
As a user, I want to **import/export puzzles** so I can share them with others.  
- **Acceptance Criteria:**  
  - Export produces a JSON or text file with puzzle data.  
  - Import validates solvability before loading.  
  - Imported puzzles can be played immediately.  

---

## 2. Gameplay Assistance

### User Story 2.1  
As a user, I want to **see possible numbers for a cell** so I can make informed moves.  
- **Acceptance Criteria:**  
  - Clicking a cell shows candidate numbers.  
  - Candidates update dynamically as puzzle progresses.  

### User Story 2.2  
As a user, I want to **use pencil marks** so I can track possible options.  
- **Acceptance Criteria:**  
  - Pencil marks are visually distinct from confirmed entries.  
  - Pencil marks can be added/removed easily.  

### User Story 2.3  
As a user, I want to **request hints** so I can progress when stuck.  
- **Acceptance Criteria:**  
  - Hint reveals a valid move.  
  - Hint usage is tracked.  
  - Configurable limit on hints per game.  

### User Story 2.4  
As a user, I want to **undo/redo moves** so I can correct mistakes.  
- **Acceptance Criteria:**  
  - Undo reverts last move.  
  - Redo restores undone move.  
  - Unlimited undo/redo stack.  

---

## 3. Tracking & Analytics

### User Story 3.1  
As a user, I want to **track my time** so I know how long solving takes.  
- **Acceptance Criteria:**  
  - Timer starts when puzzle begins.  
  - Timer pauses when game is saved.  
  - Timer resumes when game is loaded.  

### User Story 3.2  
As a user, I want to **see statistics** so I can measure performance.  
- **Acceptance Criteria:**  
  - Statistics include time, moves, hints used.  
  - Summary shown at puzzle completion.  
  - Statistics stored with save file.  

---

## 4. User Interface

### User Story 4.1  
As a user, I want a **clear grid display** so I can easily play.  
- **Acceptance Criteria:**  
  - Grid adapts to puzzle type  
  - Selected cell, row, column, and region are highlighted.  

### User Story 4.2  
As a user, I want **customizable themes** so I can adjust for comfort.  
- **Acceptance Criteria:**  
  - Light/dark mode available.  
  - Adjustable font sizes.  
  - Color themes configurable.  

---

## 5. Technical Requirements

### User Story 5.1  
As a developer, I want a **modular architecture** so I can extend easily.  
- **Acceptance Criteria:**  
  - Separate modules for generation, solving, UI, persistence, statistics.  
  - Clear documentation for each module.  

### User Story 5.2  
As a developer, I want **efficient solving algorithms** so large puzzles are playable.  
- **Acceptance Criteria:**  
  - Solver handles grids within reasonable time.  
  - Uses backtracking + constraint propagation.  

---

## 6. Future Enhancements (Optional Roadmap)

- Multiplayer timed challenges.  
- Online puzzle sharing & leaderboards.  
- Puzzle editor for custom rule sets.  
- Mobile‑friendly UI.  
- Cloud save integration.  

---