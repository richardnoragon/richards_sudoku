# **📄 Governance Review Template**

## Development-stage evidence

When applying this template, record the candidate revision, intended stage, and
linked evidence against [alpha.md](alpha.md). Copy the actual assessment from
[PROJECT_STATUS.md](PROJECT_STATUS.md); unfilled fields and version numbers do not
prove Alpha, Beta, or release readiness.

Reusable template; fill in owners, dates, applicable checks, and evidence for each use.
This is not a completed project audit. The [versioning policy](Versioning%20%20Standard%20%20Policy.md)
and [CI enforcement plan](CI%20Enforcement%20Plan.md) define the current project scope.
API/container checks are conditional; automated version and changelog checks remain future work.

## 1. Review Context
- Standard or policy under review (e.g., **Versioning Policy**).  
- Review date: YYYY‑MM‑DD  
- Reviewer(s): Names and roles.  
- Review cycle: Annual / Semi‑annual / Ad‑hoc.  

---

## 2. Scope
- Systems, repositories, or teams included in this review.  
- Dependencies or external integrations considered.  
- Exclusions (if any).  

---

## 3. Compliance Checklist
- **Versioning compliance** verified.  
- **Changelog discipline** enforced across all releases.  
- **API versioning** consistent and documented.  
- **Database/schema migrations** tracked and reversible.  
- **Infrastructure artifacts** tagged immutably (no `latest`).  
- **CI/CD enforcement** active and validated.  

---

## 4. Evidence
- Links to changelogs, commits, or release notes.  
- CI/CD pipeline logs.  
- Documentation updates.  
- Metrics dashboards.  

---

## 5. Findings
- Strengths: Areas of strong compliance.  
- Concerns: Gaps or risks identified.  
- Required changes: Specific corrective actions.  

---

## 6. Decisions
- Approved: Policy remains valid.  
- Conditional: Policy valid with required changes.  
- Rejected: Policy requires revision or replacement.  

---

## 7. Action Items
- Assigned owners for corrective actions.  
- Deadlines for resolution.  
- Escalation paths for unresolved issues.  

---

## 8. Communication
- Summary shared with stakeholders.  
- Documentation updated to reflect review outcomes.  
- Training or guidance provided if needed.  

---

## 9. Metrics
- Compliance rate (% of repos/projects aligned).  
- Number of violations detected.  
- Resolution time for corrective actions.  

---

## 10. Changelog
- Track revisions to this review template.  
- Record updates from each governance cycle.  

---
