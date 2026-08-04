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

## Planned

### 0.2.2 — Sprint 2.1b RKM generation (Stage C)
### 0.2.3 — Sprint 2.2 gap analysis (Stage D)
### 0.2.4 — Sprint 2.3 workspace + publish (Stage E)
### 0.2.5 — Hardening (Stage F)

---

## Future (Phase 3+)
- Architecture Recommendation Engine
- Proposal Generator
- PowerPoint Generator
- Statement of Work Generator
- BOM Intelligence
- Knowledge Engine / RAG platform
