# Phase 3 Architecture Decisions

Namespace: **ATLAS-031+** (same atlas-wide log as Phase 1/2).  
Former draft labels ADR-017…024 are retired — see mapping below.

Sprint **3.0** (2026-08-09) locked the integration choices below before Sprint 3.1 coding.

---

## ATLAS-031 — Phase 3 API namespace under projects

**Status:** Accepted (Sprint 3.0)  
**Date:** 2026-08-09  

**Decision:** All Phase 3 HTTP APIs live under `/api/v1/projects/{project_id}/…`, consistent with Phase 2.

**Do not** introduce a parallel top-level `/api/v1/solutions/{projectId}/…` surface.

**Canonical prefixes (target):**

| Area | Prefix |
|------|--------|
| Domains | `/projects/{id}/domains` |
| Architectures | `/projects/{id}/architectures` (MVP today: `/architecture`) |
| Traceability | `/projects/{id}/traceability` |
| Risks / assumptions | `/projects/{id}/risks`, `/projects/{id}/assumptions` |
| BOM | `/projects/{id}/bom` |
| Vendor catalogue | `/vendors/catalogue` (global, not project-scoped) |

**MVP note:** Existing `GET/POST …/architecture` and `…/architecture/generate` remain until Sprint 3.2 migrates to plural `/architectures` (see ATLAS-034).

---

## ATLAS-032 — Phase 3 persistence uses normalized tables; reuse `projects`

**Status:** Accepted (Sprint 3.0)  
**Date:** 2026-08-09  

**Decision:**

1. Use the existing `projects` table as the solution project. Do **not** create `solution_projects`.
2. Persist Phase 3 domain objects in **normalized tables** (domains, architecture options/components, traceability, risks, assumptions, vendor/BOM entities as each sprint lands).
3. Treat `architecture_models.payload_json` as a **transitional MVP store**. Do not grow it as the long-term model. Sprint 3.2 refactors architecture generation onto normalized tables (ATLAS-034).

**Rules unchanged:** Published RKM immutable; architecture versions pin `rkm_id` + `rkm_version_label`; catalogue/BOM rows keep source + timestamp.

---

## ATLAS-033 — Phase 3 decision IDs use ATLAS-031+

**Status:** Accepted (Sprint 3.0)  
**Date:** 2026-08-09  

**Decision:** Phase 3 ADRs use the ATLAS namespace continuing after Phase 2 (ATLAS-030). Draft IDs ADR-017…024 are retired.

| Retired draft | Replacement |
|---------------|-------------|
| ADR-017 RKM authoritative | Covered by **ATLAS-023** (reaffirmed) |
| ADR-018 Vendor neutrality first | **ATLAS-035** |
| ADR-019 Evidence traceability | **ATLAS-036** |
| ADR-020 AI requires review | **ATLAS-037** |
| ADR-021 Catalogue versioned | **ATLAS-038** |
| ADR-022 External BOM is evidence | **ATLAS-039** |
| ADR-023 Multi-domain support | **ATLAS-040** |
| ADR-024 Provider independence | Covered by existing AIProvider + **ATLAS-041** |

---

## ATLAS-034 — Thin architecture MVP retained until Sprint 3.2

**Status:** Accepted (Sprint 3.0)  
**Date:** 2026-08-09  

**Decision:** Keep the shipped Published-RKM architecture generate/get MVP for demos and ATLAS-023 enforcement.

- Sprint **3.1** adds domains + traceability **alongside** the MVP; do not rewrite the MVP in 3.1.
- Sprint **3.2** refactors candidate architecture generation onto normalized tables and migrates clients to `/architectures`.
- Until that migration, new domain/traceability code must still consume **Published RKM only** and must not read customer documents.

---

## ATLAS-023 (reaffirmed) — Published RKM is authoritative for Phase 3

**Status:** Accepted (Phase 2; reaffirmed Sprint 3.0)

Architecture, domains, and vendor mapping consume a **Published** RKM version only. No Architecture Engine may read customer documents directly.

---

## ATLAS-035 — Vendor neutrality first

**Status:** Accepted  

Design capability and architecture before product selection. Vendor/product mapping is Sprint 3.3.

---

## ATLAS-036 — Evidence / requirement traceability

**Status:** Accepted  

Every architecture component must trace to requirements or a documented design dependency. A recommended architecture cannot be Complete if critical requirements are uncovered.

---

## ATLAS-037 — AI recommendations require human review

**Status:** Accepted  

AI cannot approve an architecture. Approval uses the Approver role (same RBAC family as RKM publish) unless a future decision adds a Solution Architect role.

---

## ATLAS-038 — Catalogue data is versioned

**Status:** Accepted  

Vendor/product information must retain source and date. Stale data must be flagged.

---

## ATLAS-039 — External BOM is evidence

**Status:** Accepted  

Imported distributor/vendor BOMs are inputs for validation, not unquestioned truth.

---

## ATLAS-040 — Multi-domain support

**Status:** Accepted  

Support IT and non-IT enterprise domains including AV, LED, digital signage, and smart building.

---

## ATLAS-041 — AI provider independence

**Status:** Accepted  

AI services are accessed only through the `AIProvider` abstraction so domain logic is not locked to one model vendor.
