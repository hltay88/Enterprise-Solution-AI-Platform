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

- [x] Requirement extraction → structured items
- [x] Requirement classification
- [x] Evidence mapping (`document` / `sales_intake` / …)
- [x] Draft Requirement Knowledge Model persistence
- [x] Sales intake → RKM mapping
- [x] Requirement repository / Draft RKM API

**Deliverable:** Draft RKM generated and readable in UI.  
**Evidence:** `/api/v1/projects/{id}/requirements*`; `RkmPanel`; `backend/tests/test_rkm_*.py`.

---

## Sprint 2.2 — Gap Analysis (Stage D)

- [x] Missing information detection
- [x] Completeness score
- [x] Confidence score
- [x] Dependency / conflict detection (MVP)
- [x] Requirement validation (publish blockers)
- [x] Clarification question generator
- [x] Clarification answers → RKM minor version

**Deliverable:** Gap Analysis Engine.  
**Evidence:** `/api/v1/.../gap-analysis` + clarification generate/answer; `GapAnalysisPanel`; `backend/tests/test_gap_*.py`.

---

## Sprint 2.3 — Interactive Workshop (Stage E)

- [x] Requirement editing (Draft)
- [x] Requirement timeline / version history
- [x] Version compare (MVP)
- [x] AI reasoning viewer
- [x] Approval workflow
- [x] Publish RKM (immutable)
- [ ] AI requirement chat (Draft-only, optional)

**Deliverable:** Interactive Requirement Workspace.  
**Evidence:** `/api/v1/.../requirements/review|approve|publish|compare|version`; `RkmGovernancePanel`; `backend/tests/test_governance_helpers.py`.

---

## Stage F — Hardening

- [x] Audit trail for upload / edit / approve / publish
- [x] RBAC MVP (Editor + Approver)
- [ ] Performance targets validated (100-page PDF load test — deferred)
- [x] Security checklist (Phase 2) — baseline roles/audit/secrets (full pen-test deferred)
- [x] Regression test suite green (unit: gap + governance + rbac + packs + audit schema)
- [x] Knowledge Pack stub injection (vendor-neutral)

**Evidence:** `audit_logs` + `GET /api/v1/projects/{id}/audit-logs`; `users.role`; `knowledge/networking|wireless` stubs; `backend/tests/test_rbac_roles.py`, `test_knowledge_pack_stub.py`, `test_audit_schema.py`; `AuditLogPanel`.
