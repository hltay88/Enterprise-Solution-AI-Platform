# DECISIONS_PHASE2.md
Phase 2 Architecture Decisions

---

## Decision 011 — Requirement Knowledge Model
**Status:** Accepted
**Decision:** The Requirement Knowledge Model (RKM) becomes the canonical business object for Project Atlas.
**Reason:** All downstream modules require a consistent representation of customer requirements.

---

## Decision 012 — Evidence Traceability
**Status:** Accepted
**Decision:** Every requirement must reference supporting evidence from uploaded documents.
**Reason:** Provides auditability and prevents AI hallucination.

---

## Decision 013 — Human Approval Required
**Status:** Accepted
**Decision:** AI may propose Requirement Knowledge Models but cannot publish them.
**Reason:** Business accountability remains with human reviewers.

---

## Decision 014 — Single Source of Truth
**Status:** Accepted
**Decision:** Every downstream module consumes the published RKM.
**Reason:** Eliminates repeated document parsing and inconsistent interpretations.

---

## Decision 015 — Version Immutability
**Status:** Accepted
**Decision:** Published Requirement Knowledge Models cannot be modified. Changes require a new version.
**Reason:** Supports traceability, auditing, and governance.

---

## Decision 016 — Phase Separation
**Status:** Accepted
**Decision:** Phase 2 focuses solely on business understanding. Architecture, proposal generation, BOM generation, and vendor recommendations begin only in later phases.
**Reason:** Separating analysis from solution generation improves accuracy and maintainability.
