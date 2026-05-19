
> **Governance cross-references:** Parent: [speckit.constitution](speckit.constitution) §3 & §6 | Lifecycle: [C.L.E.A.R. Lifecycle Table](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md) | Enforced by: [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) §3 | CI checks: [CI Enforcement Plan](CI%20Enforcement%20Plan.md) | Related: [Appendix A](speckit.constitution.appendix.a.md) (quality standards), [Appendix D](speckit.constitution.appendix.d.md) (performance budgets)

# **Appendix B — Testing Matrix & Fixtures**

## **B1. Coverage Matrix**
Every release must satisfy the following coverage:

| Area | Required Tests |
|------|----------------|
| Solver | correctness, conflict detection, deterministic behavior |
| Generator | uniqueness, solvability, seed determinism |
| Persistence | save/load round‑trip, schema migration, malformed payload rejection |
| SE Difficulty | boundary scores, known fixtures, per‑technique minimal cases |
| Variants | Standard, Jigsaw, Str8ts, Killer, 1–25, Codewords, KenKen, Kakuro |
| UI | smoke tests: rendering, selection, highlight, undo/redo, hints |
| Performance | solver latency, generator latency, import/export latency |

## **B2. Fixture Requirements**
- **Known difficulty fixtures** for SE grading (easy, medium, hard, expert).
- **Minimal technique fixtures**: one per SE technique.
- **Variant fixtures**: at least 3 per variant (easy, medium, hard).
- **Regression fixtures**: import/export round‑trip for all variants.

## **B3. Performance Tests**
- 9×9 validation <200ms  
- 9×9 solve <2s  
- Save/load <300ms  
- Large variants must not exceed memory ceilings ([Appendix D](speckit.constitution.appendix.d.md))

## **B4. Property‑Based Tests**
- Randomized grids for:
  - Candidate propagation  
  - Conflict detection  
  - Region constraints  
- Multi‑variant scenario tests:
  - Str8ts runs  
  - Killer cages  
  - KenKen operations  
  - Kakuro sums  

## **B5. Determinism Enforcement**
- All tests using randomness must specify seeds.
- CI must reject nondeterministic output.

---

> **See also:** [Appendix A](speckit.constitution.appendix.a.md) — Code Quality Standards | [Appendix C](speckit.constitution.appendix.c.md) — UX Interaction Model | [Appendix D](speckit.constitution.appendix.d.md) — Performance Budgets | [Appendix E](speckit.constitution.appendix.e.md) — Serialization Schema
