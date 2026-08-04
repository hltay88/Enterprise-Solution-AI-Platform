# TASKS_PHASE2.md

Atlas Foundation 0.2  
Tracking rule: mark `[x]` only with demo evidence or automated tests.  
Roadmap: `PHASE2_ROADMAP.md`

---

## Stage A — Foundations

- [x] Lock evidence policy, API versioning, file limits, decision renumbering (ATLAS-020+)
- [x] Publish Phase 2 roadmap A→F
- [x] Reset false-complete checklists
- [x] Freeze RKM Schema v1.0 typed contract
- [x] OpenAPI stub for `/api/v1` Phase 2 routes (optional before Stage B)

---

## Sprint 2.1a — Document Intelligence (Stage B)

- [x] Multi-file upload (within ATLAS-027 limits)
- [x] PDF parser (native text)
- [x] DOCX / DOC parser
- [x] Excel / CSV parser
- [x] Image OCR (PNG/JPG; scanned PDF)
- [x] Text normalization
- [x] Metadata extraction
- [x] Duplicate detection (SHA-256)
- [x] Page / chunk persistence
- [x] Async processing job status

**Deliverable:** Working document ingest + extract pipeline.  
**Evidence:** `/api/v1/documents/*` + `/api/v1/jobs/{id}`; `backend/tests/test_parsers.py`, `test_normalize_and_chunking.py`, `test_phase2_file_types.py`.

---

## Sprint 2.1b — RKM Generation (Stage C)

- [ ] Requirement extraction → structured items
- [ ] Requirement classification
- [ ] Evidence mapping (`document` / `sales_intake` / …)
- [ ] Draft Requirement Knowledge Model persistence
- [ ] Sales intake → RKM mapping
- [ ] Requirement repository / Draft RKM API

**Deliverable:** Draft RKM generated and readable in UI.

---

## Sprint 2.2 — Gap Analysis (Stage D)

- [ ] Missing information detection
- [ ] Completeness score
- [ ] Confidence score
- [ ] Dependency / conflict detection (MVP)
- [ ] Requirement validation (publish blockers)
- [ ] Clarification question generator
- [ ] Clarification answers → RKM minor version

**Deliverable:** Gap Analysis Engine.

---

## Sprint 2.3 — Interactive Workshop (Stage E)

- [ ] Requirement editing (Draft)
- [ ] Requirement timeline / version history
- [ ] Version compare (MVP)
- [ ] AI reasoning viewer
- [ ] Approval workflow
- [ ] Publish RKM (immutable)
- [ ] AI requirement chat (Draft-only, optional)

**Deliverable:** Interactive Requirement Workspace.

---

## Stage F — Hardening

- [ ] Audit trail for upload / edit / approve / publish
- [ ] RBAC MVP (Editor + Approver)
- [ ] Performance targets validated
- [ ] Security checklist (Phase 2)
- [ ] Regression test suite green
- [ ] Knowledge Pack stub injection (vendor-neutral)
