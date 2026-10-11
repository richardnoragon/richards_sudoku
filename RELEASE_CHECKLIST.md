

## Current release status

Release approval is pending. Use [PROJECT_STATUS.md](PROJECT_STATUS.md) for implemented
behavior and open gaps, and [TESTING.md](TESTING.md#latest-local-validation) for local
results. Complete this checklist for the final release commit; historical evidence
below does not certify the current remote settings or candidate.

- [ ] Resolve or explicitly defer DOC-01 through DOC-10 with rationale and acceptance evidence.
- [ ] Record a fresh-install and manual gameplay check for each target platform.
- [ ] Attach current CI evidence and verify required-check enforcement.

# **RELEASE_CHECKLIST.md (Governance‑Enforced)**

## Development maturity gate

Use [alpha.md](alpha.md) for stage definitions. Current status is **pre-alpha**.

- [ ] All seven [Alpha criteria](PROJECT_STATUS.md#alpha-readiness) have evidence,
  including DOC-09 independent handoff and architecture stability review.
- [ ] Beta ordinary-user reliability has been demonstrated for the agreed scope.
- [ ] Candidate revision, scope, known limitations, and intended release stage are recorded.

These entries do not replace the publication requirements below. A recorded exception
cannot establish Alpha while a required primary workflow remains broken.

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
- [ ] Required CI checks are green on all three OS targets (Windows/Linux/macOS)
- [ ] Python lint/type checks are green (Ruff + mypy)
- [ ] Markdown lint is green for all repository markdown files

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
- [ ] Verify the `main` branch ruleset requires pull requests and all five current status checks for this release

---

### **9. Historical Hardening Evidence Links**

Previously recorded evidence; not revalidated during the 2026-09-29 local documentation review.
- Branch ruleset: <https://github.com/richardnoragon/richards_sudoku/settings/rules/19846804>
- Blocking verification PR (closed after validation): <https://github.com/richardnoragon/richards_sudoku/pull/1>
- Quality Gates workflow run: <https://github.com/richardnoragon/richards_sudoku/actions/runs/30296831560>
- Job links:
  - Markdown Lint: <https://github.com/richardnoragon/richards_sudoku/actions/runs/30296831560/job/90079831422>
  - Python Lint and Type: <https://github.com/richardnoragon/richards_sudoku/actions/runs/30296831560/job/90079831411>
  - Tests (ubuntu-latest): <https://github.com/richardnoragon/richards_sudoku/actions/runs/30296831560/job/90079831410>
  - Tests (windows-latest): <https://github.com/richardnoragon/richards_sudoku/actions/runs/30296831560/job/90079831429>
  - Tests (macos-latest): <https://github.com/richardnoragon/richards_sudoku/actions/runs/30296831560/job/90079831463>
- Blocking verification: direct push attempt to `main` rejected by protected-branch hook (`GH006`, `Changes must be made through a pull request`).

---
