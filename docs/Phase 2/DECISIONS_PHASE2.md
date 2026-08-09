# DECISIONS_PHASE2.md

Phase 2 Architecture Decisions  
Namespace: **ATLAS-020+** (see ATLAS-028)

> Historical note: an earlier draft used “Decision 011–016”, which collided with Sprint 1 IDs in `docs/Phase 1/DECISIONS.md`. Those draft numbers are retired.

---

## ATLAS-020 — Requirement Knowledge Model is canonical

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:** The Requirement Knowledge Model (RKM) is the canonical business object for Project Atlas Phase 2+.  

**Reason:** Downstream modules need one consistent representation of customer requirements.  

**Impact:** Uploaded documents are evidence inputs, not the system of record after publish.

---

## ATLAS-021 — Evidence traceability (source types)

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:** Every requirement MUST reference one or more evidence records. Allowed `source_type` values:

| source_type | When used |
|-------------|-----------|
| `document` | Extracted from an uploaded file (include document_id, page, excerpt when available) |
| `sales_intake` | Derived from Sprint 1.1 sales intake fields / requirement_details |
| `workshop` | Captured during interactive review / workshop notes |
| `clarification_answer` | Created or updated from a customer clarification response |

**Reason:** Preserves auditability while allowing sales-known facts that are not in uploaded RFPs (resolves conflict with intake-only analysis).  

**Impact:** “No document evidence” is valid only when another allowed source_type is present. Hallucinated requirements without evidence are rejected.

---

## ATLAS-022 — Human approval required to publish

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:** AI may propose Draft RKMs and suggest edits. AI cannot publish. Human approval is mandatory before publish.  

**Reason:** Business accountability remains with human reviewers.

---

## ATLAS-023 — Published RKM is the single source of truth for downstream

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:** Phase 3+ engines consume only **Published** RKMs. They must not parse uploaded customer documents directly.  

**Reason:** Eliminates repeated parsing and inconsistent interpretations.

---

## ATLAS-024 — Version immutability

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:**

- A project has at most one **Active Draft** RKM and at most one **Published** RKM.
- Published RKMs are immutable.
- Edits require a new version (major / minor / patch per `VERSIONING.md`).
- Historical versions remain readable.

**Reason:** Traceability, auditing, and governance.

---

## ATLAS-025 — Phase separation

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:** Phase 2 focuses solely on business understanding (RKM). Architecture, proposal, BOM, and vendor/product recommendations begin in later phases.  

**Reason:** Separating analysis from solution generation improves accuracy and maintainability.

---

## ATLAS-026 — API versioning for Phase 2

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:**

- Keep Sprint 1 endpoints under `/api/*` for compatibility during transition.
- Ship Phase 2 Requirement Intelligence APIs under `/api/v1/*` as defined in `API_PHASE2.md`.
- Do not silently break Sprint 1 clients.
- Deprecate Sprint 1 analyze/clarification flat endpoints only after RKM path is accepted.

**Reason:** Avoids a breaking rewrite while allowing a clean Phase 2 contract.

---

## ATLAS-027 — Phase 2.1 file limits and types

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision (Phase 2.1):**

- Max **50 MB** per file
- Max **200 MB** aggregate per upload batch / project processing batch
- Allowed types: PDF, DOCX, DOC, XLSX, CSV, TXT, PNG, JPG, JPEG
- Virus scan remains required before processing (tooling choice deferred to implementation ADR)
- ZIP, PPTX, TIFF, Visio exports: deferred after 2.1

**Reason:** Balances real Presales RFPs against Mac Docker / OCR cost and timeout risk. Supersedes Sprint 1’s 10 MB limit for Phase 2 paths; Sprint 1 upload path may remain at 10 MB until migrated.

---

## ATLAS-028 — Decision ID renumbering

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:** All Phase 2 architecture decisions use **ATLAS-020+** in both `docs/Phase 2/DECISIONS_PHASE2.md` and the main `docs/Phase 1/DECISIONS.md` log.  

**Reason:** Removes collision with Sprint 1 ATLAS-011…015a.

---

## ATLAS-029 — Async processing for heavy Phase 2 jobs

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:** OCR, multi-document extraction, and RKM generation run as **asynchronous jobs** with status polling (or equivalent). Synchronous HTTP must not be the only path for large documents.  

**Reason:** Performance targets (100-page PDF &lt; 120s wall-clock) and UX require progress/retry without blocking API workers indefinitely.  

**Implementation choice** (queue library / worker) may be recorded in a follow-up ADR during Stage B.

---

## ATLAS-030 — Embeddings / vector DB deferred

**Status:** Accepted  
**Date:** 2026-08-04  

**Decision:** `document_embeddings` / vector RAG are **out of scope for Sprint 2.1**. Chunk storage may exist without embeddings. Revisit when Knowledge Pack retrieval needs RAG.  

**Reason:** Avoid platform complexity before RKM core works.
