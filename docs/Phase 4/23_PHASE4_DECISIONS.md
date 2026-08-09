# Phase 4 Architecture Decisions

Namespace: **ATLAS-042+** (same atlas-wide log as Phase 1–3).  
Former outline labels ADR-025…031 are retired — see mapping below.

Sprint **4.0** (2026-08-10) locked the integration choices below before Sprint 4.1 coding.

---

## Sprint 4.0 locks

| Lock | Decision |
|------|----------|
| **L1 Input gate** | Require Published RKM + architecture `status=complete`. Validated BOM optional for Proposal (explicit assumption / REVIEW REQUIRED if absent; no invented prices). Validated BOM required later for package/commercial sections (Sprint 4.4). |
| **L2 Decision IDs** | ATLAS-042+ (retire ADR-025…031). |
| **L3 Render stack (4.1)** | DOCX via `python-docx` write path. PPTX → 4.2. PDF → 4.3. XLSX → 4.4. |
| **L4 RBAC (4.1)** | Author/Reviewer edits → `editor`. Document approve → `approver`. Full six-role matrix deferred. |
| **L5 API / naming** | Phase 4 deliverables under `/api/v1/projects/{id}/deliverables/...`. Do not overwrite Phase 2 `/documents` ingest. DB root entity: `generated_documents`. |

---

## ATLAS-042 — Deliverables API under projects (not Phase 2 documents)

**Status:** Accepted (Sprint 4.0)  
**Date:** 2026-08-10  

**Decision:** Generated customer-facing documents use `/api/v1/projects/{project_id}/deliverables/...`.

Phase 2 retains `/documents` for requirement file ingest (`requirement_documents`).

---

## ATLAS-043 — Immutable source snapshot per generation run

**Status:** Accepted (Sprint 4.0)  
**Date:** 2026-08-10  

**Decision:** Every generation run creates an immutable `source_snapshots` row pinning RKM, architecture, optional BOM/catalogue versions, prompt/model/template metadata. Document versions reference exactly one snapshot. Never silently mix source versions.

---

## ATLAS-044 — AI structured content; separate rendering

**Status:** Accepted (Sprint 4.0)  
**Date:** 2026-08-10  

**Decision:** AI (behind `AIProvider`) emits schema-validated structured content only. Rendering engines produce DOCX/PDF/PPTX/XLSX from approved content + versioned templates with no AI dependency.

---

## ATLAS-045 — Human approval for customer-facing deliverables

**Status:** Accepted (Sprint 4.0)  
**Date:** 2026-08-10  

**Decision:** Approver role must approve before a deliverable version is `approved`. Approved versions are immutable; revisions create a new version and require re-review.

---

## ATLAS-046 — Templates versioned independently

**Status:** Accepted (Sprint 4.0)  
**Date:** 2026-08-10  

**Decision:** `document_templates` / `template_versions` are versioned independently from document versions. Historical exports retain the template version used at render time.

---

## ATLAS-047 — No commercial/contractual fabrication

**Status:** Accepted (Sprint 4.0)  
**Date:** 2026-08-10  

**Decision:** Prices, discounts, warranties, contractual dates, and SLAs require authoritative approved data in the source snapshot. Otherwise mark REVIEW REQUIRED or omit — never invent.

---

## ATLAS-048 — AI provider abstraction retained

**Status:** Accepted (Sprint 4.0)  
**Date:** 2026-08-10  

**Decision:** Phase 4 generation methods extend `AIProvider`. Domain logic stays in services + Pydantic schemas, not prompts or UI.

---

## Retired outline IDs

| Retired draft | Replacement |
|---------------|-------------|
| ADR-025 Source snapshot | **ATLAS-043** |
| ADR-026 AI content / render split | **ATLAS-044** |
| ADR-027 Human approval | **ATLAS-045** |
| ADR-028 Versioned templates | **ATLAS-046** |
| ADR-029 Shared solution snapshot | Covered by **ATLAS-043** |
| ADR-030 Authoritative commercial data | **ATLAS-047** |
| ADR-031 Provider abstraction | **ATLAS-048** (+ ATLAS-041) |
