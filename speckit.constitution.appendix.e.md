---

> **Governance cross-references:** Parent: [speckit.constitution](speckit.constitution) §2.6 & §6 | Lifecycle: [C.L.E.A.R. Lifecycle Table](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md) | Enforced by: [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) §6 | CI checks: [CI Enforcement Plan](CI%20Enforcement%20Plan.md) | Migration history: [MIGRATIONS.md](MIGRATIONS.md) | Related: [Appendix A](speckit.constitution.appendix.a.md) §A5 (serialization discipline)

# **Appendix E — Serialization Schema & Migration Rules**

## **E1. Schema Versioning**
- All save files include:
  ```json
  {
    "schema_version": <int>,
    ...
  }
  ```
- Increment schema version when:
  - Adding fields  
  - Changing field semantics  
  - Changing variant descriptors  

## **E2. Backward Compatibility**
- Loaders must:
  - Accept all previous schema versions  
  - Apply migrations automatically  
  - Reject malformed payloads safely  

## **E3. Required Fields**
Every save file must contain:

| Field | Description |
|-------|-------------|
| `schema_version` | integer |
| `variant` | string identifier |
| `grid` | serialized grid state |
| `pencil_marks` | optional |
| `stats` | moves, hints, timer |
| `se_score` | optional |
| `se_label` | optional |

## **E4. Migration Table**
Each schema version must define:

- Added fields  
- Removed fields  
- Default values for missing fields  
- Transformation rules  

Example:

| Version | Change |
|---------|--------|
| 3 → 4 | Added `se_score`, `se_label` |
| 4 → 5 | Added `variant_settings` block |
| 5 → 6 | Normalized region descriptors |

## **E5. Validation Rules**
- Reject if:
  - Grid size mismatches variant  
  - Region map invalid  
  - Pencil marks contain invalid digits  
  - Stats contain negative values  

## **E6. Security**
- No executable content permitted in payloads.
- No external references (URLs, file paths).
- All strings must be sanitized.

---

> **See also:** [Appendix A](speckit.constitution.appendix.a.md) — Code Quality Standards (§A5 Serialization Discipline) | [Appendix B](speckit.constitution.appendix.b.md) — Testing Matrix (persistence tests) | [Appendix C](speckit.constitution.appendix.c.md) — UX Interaction Model (§C5 Persistence UX) | [Appendix D](speckit.constitution.appendix.d.md) — Performance Budgets (§D3 Persistence Latency) | [MIGRATIONS.md](MIGRATIONS.md) — Schema Migration History | [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) §6
