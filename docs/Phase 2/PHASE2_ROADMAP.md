# PHASE2_ROADMAP.md

Phase: Atlas Foundation 0.2 — Requirement Intelligence Engine  
Status: Approved for execution (Stage A foundations first)  
Related: `TASKS_PHASE2.md`, `PHASE2_ACCEPTANCE.md`, `DECISIONS_PHASE2.md`, `IMPLEMENTATION_GUIDE.md`

---

## Locked conflict resolutions (Stage A)

| Topic | Decision ID | Lock |
|-------|-------------|------|
| Decision ID namespace | ATLAS-028 | Phase 2 decisions use **ATLAS-020+** (not Decision 011–016) |
| Evidence policy | ATLAS-021 | Every requirement needs evidence; `source_type` may be `document`, `sales_intake`, `workshop`, or `clarification_answer` |
| API versioning | ATLAS-026 | Sprint 1 stays on `/api/*`; Phase 2 resources ship under `/api/v1/*` |
| File limits (Phase 2.1) | ATLAS-027 | **50 MB / file**, **200 MB / project batch**; types listed below |

Phase 2.1 allowed file types: `PDF`, `DOCX`, `DOC`, `XLSX`, `CSV`, `TXT`, `PNG`, `JPG`, `JPEG`.  
ZIP / PPTX / TIFF / Visio are **deferred** past 2.1.

---

## Delivery stages (A → F)

### Stage A — Foundations (docs + contracts) — **DONE**
- Renumber / record ATLAS-020+ decisions
- Reset false-complete task/acceptance checkboxes
- Freeze RKM JSON Schema v1.0 (typed)
- Align API, file, evidence docs to locks above
- **Exit:** Stage A PR merged; no application feature code required

### Stage B — Sprint 2.1a Document Intelligence (ingest) — **IN PROGRESS**
- Multi-file upload within locked limits
- Native text extraction + OCR for images / scanned PDFs only
- SHA-256 checksum, basic duplicate detection
- Page/chunk + metadata persistence (minimal)
- **Exit:** multi-file ingest + extract on sample RFP set

### Stage C — Sprint 2.1b RKM Generation
- AI extraction → structured requirements + classification + evidence refs
- Persist Draft RKM (`requirement_models`, `requirements`, `requirement_evidence`)
- Map Sprint 1.1 sales intake into RKM project/stakeholders/details
- **Exit:** Draft RKM viewable with evidence links

### Stage D — Sprint 2.2 Gap Analysis
- Deterministic completeness + confidence scoring first
- Gap report + clarification generation (priority, reason, affected requirement)
- Clarification answers create a new RKM **minor** version
- **Exit:** scores + clarification round-trip on Draft RKM

### Stage E — Sprint 2.3 Workspace & Governance
- Requirement edit UI, version timeline/compare, reasoning viewer
- Review → approve → publish; published RKM immutable
- Optional AI chat **Draft-only**
- **Exit:** publish gate enforced; Phase 3 can fetch published RKM only

### Stage F — Hardening
- Audit log, RBAC MVP (Editor + Approver minimum)
- Performance pass (100-page PDF targets), security checklist, regression suite
- Knowledge Pack stub injection (vendor-neutral) after RKM stable
- **Exit:** `PHASE2_ACCEPTANCE.md` metrics met with real tests

---

## Explicit non-goals until Phase 3

Architecture, proposal, PowerPoint, SOW, BOM, vendor/product recommendation, full Entra ID SSO, vector RAG platform.

---

## Execution rule

1. Complete Stage A before Stage B code.
2. Do not mark TASKS / ACCEPTANCE items complete without tests or demo evidence.
3. Any change to locked decisions requires a new ATLAS decision entry.
