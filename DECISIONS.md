# Architectural Decisions

## Full rebrand (2026-10-10)

The project, command, repository target, and workspace are `sudoku-inator`;
the Python package is `sudoku_inator`. This supersedes decision 1 below, which
is preserved as a historical record. The former import path and command are
retired; JSON save schemas and application version remain unchanged.
See [REBRANDING.md](REBRANDING.md) for migration and verification.

## Alpha workflow decisions (2026-10-01)

- Stabilize the five existing interactive hint modes; defer Multi-reveal and
  Walkthrough. Unknown modes return failure without spending allowance.
- Keep undo history session-local. Preserve notes and original clues in JSON;
  compute remaining hints from the configured limit and recorded usage.
- Store Codewords hypotheses on Board, separately from the solution mapping;
  use CodebookMove in the shared undo stack.
- Share partial-board validation across rendering, Check Board, and completion.
  Variant-specific generation consumes the worker result instead of regenerating.
- Use bounded variant search for clue removal: timeout/node exhaustion means
  retain the clue, never claim uniqueness. Kakuro may have given digits. Str8ts
  currently uses cyclic consecutive layouts; wider variety remains planned.
- Architecture assessment for this change: existing UI/controller/model/services/
  persistence boundaries remain usable; validation/search responsibilities now
  have shared services. No major rewrite was needed. This is the implementing
  agent's assessment, not the independent DOC-09 review.

## Alpha alignment

Use [alpha.md](alpha.md) when reviewing architecture stability for DOC-09. Record
any expected major rewrite, unsettled storage/configuration decision, or scope
change before marking the Alpha architecture criterion satisfied.

## Implementation boundary

These decisions describe the architectural direction. The registry, controller,
and service boundaries exist, but UI/controller/model code still includes explicit
variant branches. Adding a variant requires changes and tests across those layers.
See [ARCHITECTURE.md](ARCHITECTURE.md) for current interfaces and
[PROJECT_STATUS.md](PROJECT_STATUS.md) for unresolved behavior.


## 1. Public branding stays distinct from internal package naming
Decision: The product is branded as Sudoku-inator in user-facing documentation, while the internal Python package continues to use `richards_sudoku`.

Why:
- Preserves compatibility with the existing package layout, imports, and tooling.
- Keeps the codebase stable while supporting a cleaner product identity.
- Reduces churn during rebranding and avoids breaking scripts or tests.

Impact:
- README and product docs use Sudoku-inator
- Python modules and package imports remain unchanged unless an explicit refactor is planned

---

## 2. Central controller owns runtime state
Decision: The `GameController` is the runtime hub for board state, puzzle lifecycle, timer, stats, history, and save/load orchestration.

Why:
- It keeps application state in one place and prevents UI logic from becoming the source of truth.
- It simplifies event handling between board widgets, dialogs, and service modules.
- It creates a clear boundary between presentation and game logic.

Impact:
- UI widgets remain focused on interaction and rendering
- Controller methods become the canonical orchestration point for gameplay behavior

---

## 3. UI is deliberately thin and signal-driven
Decision: The PyQt UI layer emits signals and reacts to controller updates rather than directly owning game rules.

Why:
- Prevents the UI from becoming tightly coupled to gameplay logic.
- Enables easier testing and cleaner separation of responsibilities.
- Supports keyboard, accessibility, and theme workflows without deep rule logic in widgets.

Impact:
- Signals such as selection and value entry are the bridge between UI and controller
- The UI can be reworked or extended without rewriting the core rules engine

---

## 4. The solver/generation layer is isolated from the UI
Decision: When generating or solving puzzles, the system delegates to `solver/` and `services/` modules instead of baking logic into the UI or controller.

Why:
- Puzzle generation and validation are complex and variant-specific.
- Keeping them separate reduces accidental coupling and makes testing easier.
- It allows variant-specific logic to evolve independently from the app shell.

Impact:
- New variants can be added by expanding generation and validation modules
- UI code remains mostly agnostic to puzzle complexity and constraint rules

---

## 5. Persistence uses versioned JSON documents instead of a relational database
Decision: Game state is saved as structured JSON with explicit schema versioning.

Why:
- The app is a desktop tool, not a multi-user transactional system.
- Save files need to be portable and easy to inspect.
- Schema versioning provides migration paths for future changes.

Impact:
- Save files are self-contained
- The project can evolve without breaking old saves unexpectedly

---

## 6. Shared services are cross-cutting utilities, not UI logic
Decision: Candidate calculation, timers, stats, undo/redo, and difficulty grading remain in the `services/` layer.

Why:
- These are reusable across multiple gameplay flows and screens.
- They are not inherently tied to one widget or one dialogue.
- They are easier to validate in isolation than if embedded in UI code.

Impact:
- New features can reuse the same support services without duplicating logic
- Testing is more straightforward because the services are independent of UI state

---

## 7. Variant behavior is metadata-driven
Decision: Variant-specific configuration is expressed in metadata and registry entries rather than hard-coded in many controller branches.

Why:
- Variant diversity is central to the project.
- Rule constraints differ by puzzle type, but the controller should not become a long if/else tree.
- Registry-driven metadata supports extensibility and cleaner reuse.

Impact:
- New puzzle types start with registry definitions and also require solver, controller, UI, persistence, and test integration
- The controller stays focused on orchestration instead of variant mechanics

---

## 8. Event communication uses Qt signals and callback hooks
Decision: The app uses Qt signals for user-driven changes and callback hooks for high-level completion or refresh events.

Why:
- It fits naturally with PyQt application architecture.
- It keeps the communication model lightweight and explicit.
- It avoids introducing a bigger framework where a single-window app does not need one.

Impact:
- UI events flow into the controller cleanly
- Completion and refresh actions remain decoupled from direct widget internals

---

## 9. Future extensibility should happen through modules, not rewrites
Decision: Additional puzzle types, services, and UI features should be added through modular extensions rather than modifying the core game model in place.

Why:
- The project is already organized into clear subsystems.
- This reduces the risk of breaking unrelated behaviors.
- It preserves the architectural boundary between core logic and feature growth.

Impact:
- The system can evolve toward richer puzzle support, better analytics, or optional plug-ins without destabilizing the app

---

## 10. Keep the system understandable before optimizing for abstraction
Decision: We prefer explicit, maintainable code boundaries over highly abstract frameworks when the project does not require them.

Why:
- The app is a desktop game with a medium-sized codebase, not a distributed platform.
- Clear layers and focused modules are more valuable than over-engineering.
- It lowers onboarding cost for contributors and keeps logic easier to trace.

Impact:
- Architecture remains straightforward and contributor-friendly
- The project can evolve without large-scale framework churn

---

## Summary
The project’s decisions consistently favor a maintainable layered architecture: a central controller, isolated rule generation, shared services, versioned persistence, and modular variant support. This keeps the app extensible while remaining understandable and stable as the product grows.
