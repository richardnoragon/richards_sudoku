# Architecture

## Overview
Sudoku-inator is organized as a layered desktop application built around a central game hub that coordinates the user interface, gameplay logic, puzzle generation, persistence, and variant-specific rules. The architecture favors clear separation of responsibilities while keeping the runtime model simple and easy to extend.

### Current architecture status

The current implementation is a stable beta/release-candidate architecture for the project’s active feature set. The controller-driven layout, persistence layer, variant registry, and shared service boundaries are all in place and validated by the repository test suite.

At a high level:
- The UI shell provides the desktop experience.
- A central controller owns the active game state.
- Shared services handle timing, scoring, candidate updates, hints, and undo/redo.
- The model defines board, move, and variant metadata types.
- The solver and generator modules produce valid puzzles and solutions.
- Persistence stores game state in versioned JSON documents.

---

## Hub Architecture
The application follows a hub-and-spoke design centered on the game controller.

### Core hub
The primary hub is the game controller in `src/richards_sudoku/controller/game_controller.py`.
It acts as the façade between the UI and the rest of the system. It owns:
- the current board
- the active variant metadata
- the current solution and puzzle state
- the undo/redo stack
- the timer and stats trackers
- hint and completion logic
- save/load orchestration

### UI shell
`src/richards_sudoku/main.py` creates the application window and binds user actions to controller functions. The shell handles:
- menu and toolbar actions
- status bar updates
- theme toggling
- keyboard shortcuts
- board interaction events

This keeps the UI layer focused on presentation and interaction while the controller owns the rules and state transitions.

### Interaction flow
1. The user interacts with the board or dialogs in the UI.
2. The UI emits Qt signals such as selected cells, value entry, and pencil toggles.
3. The controller interprets those events and updates board state.
4. Shared services recalculate candidates, stats, timers, and validation.
5. The UI refreshes view state from the updated controller state.

---

## Plugin / Module Architecture
The project is modular rather than monolithic. Each subsystem has a focused responsibility.

### Package map
- `controller/` — orchestration and application flow
- `model/` — board, move, and variant schema types
- `persistence/` — save/load handling and data validation
- `services/` — shared utilities and cross-cutting logic
- `solver/` — validation, solving, generation, and variant generation
- `ui/` — PyQt widgets, dialogs, and styling

### Module responsibilities
#### Model layer
Defines the canonical game structures:
- board representation
- cell state
- variant enum and metadata
- move records

This layer is the source of truth for board shape, rules metadata, and invariant definitions.

#### Solver and generation layer
Responsible for puzzle validity and generation logic:
- solving and uniqueness checks
- puzzle generation from metadata
- variant-specific generator logic for Jigsaw, Str8ts, Killer, KenKen, Kakuro, Codewords, and 1-to-25

This layer is intentionally isolated so the UI and controller never need to reason about puzzle-generation internals.

#### Service layer
Shared services support gameplay and app behavior across many screens and workflows:
- candidate calculation
- hint logic support
- timer tracking
- stats collection
- undo/redo operations
- difficulty scoring
- text import/export
- variant registry lookups

#### Persistence layer
Handles state serialization and version compatibility. It is the boundary between transient runtime state and durable save files.

#### UI layer
Contains PyQt widgets and dialogs for:
- board rendering
- selection and edit operations
- new-game flows
- completion dialogs
- theme settings

---

## Database Relationships
This project does not use a traditional relational database. Instead, it persists game state as structured JSON using a versioned schema.

### Persistence model
The persistence layer uses a central `SaveState` container that groups all the data required to restore a session:
- board
- variant metadata
- solution
- timer
- stats
- SE score and label
- hint limit

### Relationship structure
The logical relationship is:
- one `SaveState` belongs to one active game session
- one `board` belongs to one `variant_meta`
- one `variant_meta` defines rules and layout for one puzzle type
- one `solution` may be associated with a board for hinting and validation
- one `timer` and one `stats` object belong to the same current run

### Schema versioning
The schema is version-aware via `model/schema.py` and `add_version`/`check_version` helpers. This allows the project to load older save files safely and migrate them to the current format.

### Data-store semantics
The persistence model behaves like a lightweight document store rather than a full database:
- state is stored as JSON documents
- files are written atomically to avoid corruption
- each saved game is self-contained and portable

---

## Shared Services
Shared services are cross-cutting capabilities that multiple modules depend on.

### Core shared services
- `GameStats` — records move counts, hints used, and other runtime metrics
- `GameTimer` — tracks active elapsed time for game sessions
- `UndoRedoStack` — manages history for reversible gameplay actions
- `compute_candidates` / `update_all_candidates` — regenerate legal candidate values
- `grade` — computes difficulty or SE score for a given puzzle state
- `REGISTRY` — central registry for variant definitions and validation rules
- `export_text` / `import_text` — text-based puzzle import/export adapters

### Why they are shared
These services are intentionally not embedded in the UI or controller because they are reused across:
- multiple exercises and turns
- save/load restore flows
- rule validation and hinting
- background generation and solving tasks

---

## Adapters
The codebase uses adapter-style boundaries to decouple internal models from external systems.

### UI adapter
The UI uses the controller as its main adapter to the game domain. The UI does not manipulate the core model directly; instead it emits events and receives updates through controller methods.

### Persistence adapter
`persistence/persistence.py` adapts runtime objects such as `Board`, `GameTimer`, `GameStats`, and `VariantMetadata` into JSON schemas and back again. This is the persistence boundary.

### Variant adapter layer
The variant registry and generator code adapt rule metadata into solver behavior. Each variant provides its own constraints and generation path without forcing the main controller to know variant-specific implementation details.

### Import/export adapters
Text-based import/export supports a bridge between internal board state and external data formats. This allows puzzle portability without coupling the solver or UI directly to a specific file format.

---

## Event Communication
The project relies primarily on Qt signals and controller callbacks for runtime communication.

### Signals in the UI
The board widget emits signals such as:
- `cell_selected`
- `value_entered`
- `pencil_toggled`

These signals represent user actions and are consumed by the `GameController`.

### Controller callback pattern
The controller can invoke completion callbacks when a puzzle is solved or when a major game state transition occurs. This keeps the UI responsive without making the game logic directly dependent on widget implementation details.

### Status flow
- UI event → controller logic → service update → model mutation → UI refresh/status display

This event pattern helps the app remain responsive and decoupled from direct model mutation from multiple code paths.

---

## Future Extensibility
The architecture is designed to support future growth without a large rewrite.

### 1. Variant plugin model
The `variant_registry` pattern is a strong foundation for adding new puzzle types. New variants can be added by registering their metadata, constraint validation, and generation behavior without touching core gameplay logic.

### 2. Service-level expansion
New services can be added for:
- analytics dashboards
- online leaderboards
- user profiles
- AI-assisted hints
- puzzle sharing
- accessibility enhancements

Because the controller centralizes orchestration, new services can be introduced without redesigning the application shell.

### 3. Persistence evolution
The versioned schema gives the project a safe path for future data migrations. This allows new fields and new save formats to be added without breaking older user saves.

### 4. UI composition
The window already separates shell chrome, board widget, and dialogs. This makes it straightforward to add panels, tools, or new game modes while preserving the same game core.

### 5. Event bus potential
If the application grows beyond a single-window app, the current signal/callback model can be expanded with a lightweight event broker or command layer without breaking the existing controller-based design.

### 6. Variant plug-in extension point
The project includes a registry-driven extension model for variant metadata and rule callbacks. In `src/richards_sudoku/services/variant_registry.py`, new variant definitions are registered through a single `register_variant()` function, which keeps the controller and UI unaware of per-variant implementation details. This allows new puzzle types to plug into the same lifecycle: factory creation, validation callback resolution, and generation support.

---

## Recommended Architectural Direction
The current design is best described as a layered desktop architecture with a central gameplay hub and pluggable rule modules. It is a strong fit for the project’s needs because it balances:
- clear separation of concerns
- extensibility for new Sudoku variants
- maintainable UI/controller boundaries
- safe persistence and future schema evolution

The key architectural principle is simple: keep the board logic and rule engine central, keep the UI thin, and treat variant behavior as a modular extension point rather than a special case in the main application flow.
