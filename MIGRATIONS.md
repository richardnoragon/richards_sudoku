# **MIGRATIONS.md**

> **Governance cross-references:** Parent: [speckit.constitution](speckit.constitution) §7 | Schema rules: [Appendix E](speckit.constitution.appendix.e.md) | Serialization discipline: [Appendix A](speckit.constitution.appendix.a.md) §A5 | Release gate: [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) §6 | Lifecycle: [C.L.E.A.R. Lifecycle Table](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md) | Enforcement: [CI Enforcement Plan](CI%20Enforcement%20Plan.md)

## **Schema Migration History**

Each entry documents a schema version change, its rationale, and its migration rules.  
All entries must comply with [Appendix E](speckit.constitution.appendix.e.md) §E4 Migration Table rules.

---

## **Version X → Y**
**Date:** YYYY‑MM‑DD  
**Author:** <name>  
**Reviewed by:** Persistence Lead + Core Maintainers  

### **Summary**
Describe the purpose of the migration.  
Example:  
> Added `se_score` and `se_label` to support difficulty grading.

---

### **Changes**
- Added fields:  
  - `field_name` (type, default)  
- Removed fields:  
  - `field_name`  
- Modified semantics:  
  - `field_name` → new meaning  

---

### **Migration Rules**
Define how older payloads are transformed.

Example:
```
if schema_version == 3:
    payload["se_score"] = null
    payload["se_label"] = null
```

---

### **Backward Compatibility**
- Loader accepts versions: X, X–1, X–2  
- Missing fields defaulted  
- Deprecated fields ignored safely  

---

### **Validation**
- Round‑trip tests added  
- Malformed payload tests updated  
- Performance impact measured  

---

### **Notes**
Any special considerations, deprecations, or future cleanup.

---