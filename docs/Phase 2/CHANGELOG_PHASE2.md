# CHANGELOG_PHASE2.md

Project Atlas — Atlas Foundation 0.2

---

## Version 0.2.0-docs — Stage A foundations

### Added
- `PHASE2_ROADMAP.md` (stages A→F)
- Locked decisions ATLAS-020 … ATLAS-030
- Typed RKM Schema v1.0 contract
- Evidence `source_type` policy (document / sales_intake / workshop / clarification_answer)
- API versioning strategy (`/api` compat + `/api/v1` Phase 2)
- Phase 2.1 file limits (50 MB / file, 200 MB batch)

### Fixed
- Retired colliding “Decision 011–016” numbering
- Reset TASKS / ACCEPTANCE checkboxes that falsely showed Phase 2 product delivery complete

### Not yet implemented in code
- OCR pipeline, structured RKM persistence, gap engine, approval/publish UI

---

## Version 0.2.1 — Stage B Document Intelligence (Sprint 2.1a)

### Added
- `/api/v1/documents/upload` multi-file ingest (ATLAS-027: 50 MB/file, 200 MB/batch)
- Async extract jobs + `GET /api/v1/jobs/{jobId}` (ATLAS-029)
- Parsers: PDF (native), DOCX, DOC, XLSX, CSV, TXT; OCR for PNG/JPG and scanned PDF
- SHA-256 duplicate detection; `document_pages` / `document_chunks` / `document_metadata`
- Frontend multi-file upload with job polling

### Notes
- Sprint 1 `/api/projects/.../upload` remains available (PDF/DOCX/TXT sync)
- Virus scan remains deferred for local demo

---

## Version 0.2.2 — Stage C Draft RKM Generation (Sprint 2.1b)

### Added
- Async `POST /api/v1/projects/{id}/requirements/analyze` (`job_type=rkm_generate`)
- `GET /api/v1/projects/{id}/requirements` (+ versions list/detail)
- Tables: `requirement_models`, `requirements`, `requirement_evidence`, `requirement_evidence_links`
- AI `extract_rkm_draft` across Gemini / OpenAI / local + prompt `rkm_extraction.txt`
- Sales intake → RKM project/stakeholders mapping; evidence `sales_intake` + `document`
- Frontend `RkmPanel` with evidence links and job polling

---

## Version 0.2.3 — Stage D Gap Analysis (Sprint 2.2)

### Added
- Deterministic completeness / confidence / consistency / evidence scoring
- `POST /api/v1/projects/{id}/requirements/gap-analysis`
- Clarification APIs: generate / list / answer under `/api/v1/projects/{id}/clarification*`
- Clarification answers create a new Draft RKM **minor** version with `clarification_answer` evidence
- Publish blockers (score thresholds + human approval gate)
- Frontend `GapAnalysisPanel` with answer → version round-trip

### Fixed
- Clarification answers now **merge into Draft RKM content** (requirement/environment/stakeholder text), not evidence links only — so the new minor version visibly reflects submitted answers

---

## Version 0.2.4 — Stage E Workspace & Governance (Sprint 2.3)

### Added
- `POST /api/v1/projects/{id}/requirements/review` — Draft edits create a **patch** version
- `POST /api/v1/projects/{id}/requirements/approve` — human approval stamp
- `POST /api/v1/projects/{id}/requirements/publish` — enforces score/gap/approval gates; published RKM immutable
- `GET /api/v1/projects/{id}/requirements?status=published` — Phase 3 consumption path
- `GET /api/v1/projects/{id}/requirements/compare?from=&to=` — version diff MVP
- `POST /api/v1/projects/{id}/requirements/version` — fork new Draft from published
- Frontend `RkmGovernancePanel` (edit, reasoning, approve, publish, compare)

### Deferred
- Draft-only AI requirement chat (optional Stage E item)
- Full audit trail / RBAC (Stage F)

---

## Planned

### 0.2.5 — Hardening (Stage F)

---

## Future (Phase 3+)
- Architecture Recommendation Engine
- Proposal Generator
- PowerPoint Generator
- Statement of Work Generator
- BOM Intelligence
- Knowledge Engine / RAG platform
