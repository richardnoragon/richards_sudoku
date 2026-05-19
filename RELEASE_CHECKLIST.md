
# **RELEASE_CHECKLIST.md (Governance‑Enforced)**

This is a **publication‑grade** checklist.  
It ensures every release respects the Constitution and all appendices.

> **Governance cross-references:** Parent: [speckit.constitution](speckit.constitution) §7 | Lifecycle: [C.L.E.A.R. Lifecycle Table](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md) | Appendices: [A](speckit.constitution.appendix.a.md) | [B](speckit.constitution.appendix.b.md) | [C](speckit.constitution.appendix.c.md) | [D](speckit.constitution.appendix.d.md) | [E](speckit.constitution.appendix.e.md) | Schema history: [MIGRATIONS.md](MIGRATIONS.md) | Enforcement: [CI Enforcement Plan](CI%20Enforcement%20Plan.md)

---

# **RELEASE_CHECKLIST.md**

## **Release Readiness Checklist**

### **1. Constitution Compliance**
- [ ] No constitutional principles violated (see [speckit.constitution](speckit.constitution))  
- [ ] All changes mapped to relevant appendices (see [C.L.E.A.R. Lifecycle Table](C.L.E.A.R.%20Lifecycle%20Table%20per%20Appendix.md))  
- [ ] All lifecycle steps (C.L.E.A.R.) completed for updated appendices  

---

### **2. [Appendix A](speckit.constitution.appendix.a.md) — Code Quality**
- [ ] Layer boundaries unchanged or explicitly approved  
- [ ] All public interfaces type‑hinted  
- [ ] No cross‑layer side effects introduced  
- [ ] SE technique registry remains declarative and stable  
- [ ] Serialization changes follow [Appendix E](speckit.constitution.appendix.e.md) rules  

---

### **3. [Appendix B](speckit.constitution.appendix.b.md) — Testing Matrix**
- [ ] Solver correctness tests pass  
- [ ] Generator uniqueness & solvability tests pass  
- [ ] Persistence round‑trip tests pass  
- [ ] SE difficulty fixtures validated  
- [ ] Variant scenario tests pass for all variants  
- [ ] UI smoke tests pass  
- [ ] Performance tests meet [Appendix D](speckit.constitution.appendix.d.md) budgets  
- [ ] No nondeterministic tests  

---

### **4. [Appendix C](speckit.constitution.appendix.c.md) — UX Interaction Model**
- [ ] Grid highlighting consistent across variants  
- [ ] Pencil/entry distinction preserved  
- [ ] Accessibility requirements met (contrast, font size, no color‑only cues)  
- [ ] Controls parity validated  
- [ ] Persistence UX validated (no silent data loss)  

---

### **5. [Appendix D](speckit.constitution.appendix.d.md) — Performance Budgets**
- [ ] Solver latency within budget  
- [ ] Generator latency within budget  
- [ ] Import/export latency within budget  
- [ ] Memory ceilings respected  
- [ ] No >10% regressions in CPU/memory profiles  

---

### **6. [Appendix E](speckit.constitution.appendix.e.md) — Serialization Schema**
- [ ] Schema version incremented if required  
- [ ] Migration entry added to [MIGRATIONS.md](MIGRATIONS.md)  
- [ ] Backward compatibility validated  
- [ ] Malformed payload rejection tested  
- [ ] No executable content or unsafe fields  

---

### **7. Documentation & Release Notes**
- [ ] Updated appendices included in release notes  
- [ ] Migration notes included (if applicable)  
- [ ] Version bump applied  

---

### **8. Final Approval**
- [ ] Core Maintainers  
- [ ] QA Lead  
- [ ] UX Lead  
- [ ] Performance Lead  
- [ ] Persistence Lead  

---
