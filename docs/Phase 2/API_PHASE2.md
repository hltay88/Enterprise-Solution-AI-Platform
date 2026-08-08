# API_PHASE2.md

Related: **ATLAS-026**

---

## Versioning strategy

| Surface | Base path | Status |
|---------|-----------|--------|
| Sprint 1 (compat) | `/api/*` | Remains available during Phase 2 transition |
| Phase 2 RKM APIs | `/api/v1/*` | Canonical for Requirement Intelligence |

Sprint 1 clients continue to use `/api/projects/...` until explicitly migrated.  
Phase 2 UI and integrations should prefer `/api/v1`.

---

## Document APIs (`/api/v1`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/upload` | Upload one or more customer documents (ATLAS-027 limits). |
| GET | `/documents/{id}` | Retrieve uploaded document metadata (+ extract status). |
| GET | `/projects/{projectId}/documents` | List project documents. |
| DELETE | `/documents/{id}` | Soft-archive/delete uploaded document (project-scoped authz). |
| GET | `/jobs/{jobId}` | Poll async OCR / analysis job status (ATLAS-029). |

---

## Requirement / RKM APIs (`/api/v1`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{projectId}/requirements/analyze` | Start async RKM generation job. |
| GET | `/projects/{projectId}/requirements` | Retrieve active Draft or Published RKM (query: `status`). |
| GET | `/projects/{projectId}/requirements/versions` | List RKM versions. |
| GET | `/projects/{projectId}/requirements/versions/{version}` | Get immutable version snapshot. |
| POST | `/projects/{projectId}/requirements/review` | Submit review edits on Draft (creates patch version). |
| POST | `/projects/{projectId}/requirements/approve` | Record human approval. |
| POST | `/projects/{projectId}/requirements/publish` | Publish approved RKM (gates enforced). |
| POST | `/projects/{projectId}/requirements/version` | Fork new Draft from Published (or a version). |
| GET | `/projects/{projectId}/requirements/compare` | Compare two versions (`from`, `to` query params). |
| POST | `/projects/{projectId}/requirements/gap-analysis` | Generate missing-information report. |

---

## Clarification APIs (`/api/v1`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{projectId}/clarification/generate` | Generate clarification questions from Draft RKM. |
| POST | `/projects/{projectId}/clarification/answer` | Submit answers; creates RKM minor version. |
| GET | `/projects/{projectId}/clarification` | List clarification questions. |

---

## Analysis APIs (`/api/v1`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/{projectId}/analysis/history` | Previous AI analysis / job results. |

---

## Envelope

Phase 2 APIs continue the Sprint 1 envelope (`success`, `data`, `error`) unless a later ADR changes ATLAS-014.

---

## Future APIs (Phase 3+)

Architecture, Proposal, Presentation, SOW, BOM — not Phase 2.
