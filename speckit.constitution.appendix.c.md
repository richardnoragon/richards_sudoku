
> **Governance cross-references:** Parent: [speckit.constitution](speckit.constitution) §4 & §6 | Lifecycle: [C.L.E.A.R. Lifecycle Table](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md) | Enforced by: [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) §4 | CI checks: [CI Enforcement Plan](CI%20Enforcement%20Plan.md) | Related: [Appendix A](speckit.constitution.appendix.a.md) (layer integrity), [Appendix B](speckit.constitution.appendix.b.md) (UI smoke tests)

# **Appendix C — UX Interaction Model**

## **C1. Grid Interaction Rules**
- Selected cell must highlight:
  - Cell  
  - Row  
  - Column  
  - Region  
- Pencil marks must be visually distinct from confirmed entries.
- Conflict indicators must not rely solely on color.

## **C2. Input Model**
- Keyboard:
  - 1–9 (or 1–25) to enter digits  
  - Backspace/Delete to clear  
  - Shift or dedicated key to toggle pencil mode  
- Mouse:
  - Click to select  
  - Right‑click or modifier for pencil mode  
- Undo/redo must behave identically across variants.

## **C3. Accessibility**
- Light/dark themes mandatory.
- Adjustable font sizes.
- Minimum contrast ratios must be met.
- No color‑only cues for:
  - Conflicts  
  - Region boundaries  
  - Pencil marks  

## **C4. Feedback & Guidance**
- Hint usage count visible.
- Invalid moves must be indicated but not block navigation.
- In‑game help must describe:
  - Controls  
  - Pencil mode  
  - Variant rules  

## **C5. Persistence UX**
- Save/load/import/export must:
  - Confirm success/failure  
  - Never discard progress without explicit consent  
  - Provide clear error messages (see [Appendix E](speckit.constitution.appendix.e.md) for serialization safety rules)  

---

> **See also:** [Appendix A](speckit.constitution.appendix.a.md) — Code Quality Standards | [Appendix B](speckit.constitution.appendix.b.md) — Testing Matrix | [Appendix D](speckit.constitution.appendix.d.md) — Performance Budgets | [Appendix E](speckit.constitution.appendix.e.md) — Serialization Schema