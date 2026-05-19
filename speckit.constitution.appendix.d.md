---

> **Governance cross-references:** Parent: [speckit.constitution](speckit.constitution) §5 & §6 | Lifecycle: [C.L.E.A.R. Lifecycle Table](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md) | Enforced by: [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) §5 | CI checks: [CI Enforcement Plan](CI%20Enforcement%20Plan.md) | Related: [Appendix B](speckit.constitution.appendix.b.md) §B3 (performance tests), [Appendix A](speckit.constitution.appendix.a.md) (quality standards)

# **Appendix D — Performance Budgets & Benchmarks**

## **D1. Solver Latency Budgets**
- 9×9 puzzle validation: **< 200ms**
- 9×9 puzzle solve (backtracking): **< 2s**
- SE `grade()` for a standard 9×9: **< 100ms**
- SE `grade()` for KenKen / Kakuro 9×9: **< 1s**
- SE `grade()` for ONE_TO_25 (25×25): **< 2s**

## **D2. Generator Latency Budgets**
- Standard 9×9 `generate_puzzle`: **< 2s**
- Jigsaw 9×9 `generate_puzzle`: **< 5s**
- Str8ts 9×9 `generate_puzzle`: **< 5s**
- Killer 9×9 `generate_puzzle`: **< 10s**
- ONE_TO_25 25×25 generation: **< 30s**
- KenKen N=9 generation: **< 30s**
- Kakuro generation: **< 30s**
- Killer cage permutation: safe for cages > 5 cells (cap at 10 000 permutations per [speckit.tasks](speckit.tasks) SE‑V3)

## **D3. Persistence Latency Budgets**
- Save/load round‑trip (any variant): **< 300ms**
- Import/export text format (any variant): **< 300ms**
- Atomic write must complete without partial‑file risk

## **D4. Memory Ceilings**
- Candidate tracking for 9×9: no quadratic blowup in undo/redo history
- Candidate tracking for 25×25 (ONE_TO_25): bounded; no O(N⁴) structures
- Rendering pipeline: no retained per‑cell allocations outside repaint cycle
- SE technique loop: no accumulated state between technique invocations

## **D5. Regression Guards**
- No single commit may regress any budget by **> 10%** without explicit approval
- CI benchmarks must run on every PR touching `solver/`, `services/`, `persistence/`, or `ui/`
- Profiling methodology: `pytest-benchmark` for unit‑level; wall‑clock timing assertions in `tests/test_performance.py`

## **D6. Profiling Methodology**
- Hot paths to instrument: `_fill_grid`, `_count_solutions`, `grade()`, `update_all_candidates`, `save`, `load`
- Benchmarks use fixed seeds for determinism (see [Appendix B](speckit.constitution.appendix.b.md) §B5)
- Results tracked in CI; dashboard updated on each minor release

---

> **See also:** [Appendix A](speckit.constitution.appendix.a.md) — Code Quality Standards | [Appendix B](speckit.constitution.appendix.b.md) — Testing Matrix (§B3 Performance Tests) | [Appendix C](speckit.constitution.appendix.c.md) — UX Interaction Model | [Appendix E](speckit.constitution.appendix.e.md) — Serialization Schema | [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) §5
