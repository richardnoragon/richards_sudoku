
---

> **Governance cross-references:** Parent: [speckit.constitution](speckit.constitution) §2 & §6 | Lifecycle: [C.L.E.A.R. Lifecycle Table](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md) | Enforced by: [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) §2 | CI checks: [CI Enforcement Plan](CI%20Enforcement%20Plan.md) | Related: [Appendix B](speckit.constitution.appendix.b.md) (test coverage), [Appendix E](speckit.constitution.appendix.e.md) (serialization rules)

# **Appendix A — Code Quality Standards**

## **A1. Layer Boundaries**
- The following layers are normative and must remain decoupled:  
  **Generation**, **Solving**, **UI**, **Persistence**, **Statistics**, **SE Difficulty Grading**.
- Cross‑layer calls are permitted only through documented interfaces.
- No layer may mutate another layer’s internal state.

## **A2. Interfaces & Contracts**
- Public functions must be type‑hinted and validated.
- All grid‑like structures must implement the shared `GridProtocol` (size, region map, candidates, set/get operations).
- SE techniques must implement the `TechniqueProtocol`:
  - `name: str`
  - `weight: int`
  - `apply(grid) -> bool`

## **A3. Readability & Maintainability**
- Prefer explicit logic over cleverness.
- Comments required for:
  - Non‑obvious solving logic  
  - Generator heuristics  
  - Variant‑specific constraint logic  
- No inline lambdas for complex logic.
- No “magic numbers” except in variant definitions.

## **A4. Determinism**
- Generators accept seeds; solvers must not depend on OS‑specific randomness.
- Floating‑point operations must not influence solver correctness.

## **A5. Serialization Discipline**
- Save format is versioned (`schema_version`).
- New fields require:
  - Incremented schema version  
  - Backward‑compatible loader  
  - Migration entry in [Appendix E](speckit.constitution.appendix.e.md) and recorded in [MIGRATIONS.md](MIGRATIONS.md)  
- Malformed payloads must fail safely.

## **A6. Extensibility Rules**
- Adding a new variant requires:
  - A variant descriptor  
  - Constraint logic  
  - Rendering rules  
  - Test fixtures (see [Appendix B](speckit.constitution.appendix.b.md) §B2 for fixture requirements)  
- No existing variant may be modified to accommodate a new one.

---

> **See also:** [Appendix B](speckit.constitution.appendix.b.md) — Testing Matrix & Fixtures | [Appendix C](speckit.constitution.appendix.c.md) — UX Interaction Model | [Appendix D](speckit.constitution.appendix.d.md) — Performance Budgets | [Appendix E](speckit.constitution.appendix.e.md) — Serialization Schema

