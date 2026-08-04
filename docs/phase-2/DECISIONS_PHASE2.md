# DECISIONS_PHASE2.md

Phase 2 Architecture Decisions

> Note: These use Decision 011–016 in the Notion source. Sprint 1 `docs/DECISIONS.md` already uses ATLAS-011…015a. Prefer ATLAS-020+ when merging into the main decision log.

---

## Decision 011

**Status:** Accepted  
**Title:** Requirement Knowledge Model

**Decision:** The Requirement Knowledge Model (RKM) becomes the canonical business object for Project Atlas.

**Reason:** All downstream modules require a consistent representation of customer requirements.

---

## Decision 012

**Status:** Accepted  
**Title:** Evidence Traceability

**Decision:** Every requirement must reference supporting evidence from uploaded documents.

**Reason:** Provides auditability and prevents AI hallucination.

---

## Decision 013

**Status:** Accepted  
**Title:** Human Approval Required

**Decision:** AI may propose Requirement Knowledge Models but cannot publish them.

**Reason:** Business accountability remains with human reviewers.

---

## Decision 014

**Status:** Accepted  
**Title:** Single Source of Truth

**Decision:** Every downstream module consumes the published RKM.

**Reason:** Eliminates repeated document parsing and inconsistent interpretations.

---

## Decision 015

**Status:** Accepted  
**Title:** Version Immutability

**Decision:** Published Requirement Knowledge Models cannot be modified. Changes require a new version.

**Reason:** Supports traceability, auditing, and governance.

---

## Decision 016

**Status:** Accepted  
**Title:** Phase Separation

**Decision:** Phase 2 focuses solely on business understanding. Architecture, proposal generation, BOM generation, and vendor recommendations begin only in later phases.

**Reason:** Separating analysis from solution generation improves accuracy and maintainability.
