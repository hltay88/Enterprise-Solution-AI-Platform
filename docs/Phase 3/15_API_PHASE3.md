# API Phase 3

Base: `/api/v1`  
**Lock (ATLAS-031):** Phase 3 routes are project-scoped under `/projects/{project_id}/…` (except global vendor catalogue).

## Implemented

### Architecture MVP (ATLAS-034)

- `POST /projects/{project_id}/architecture/generate`
- `GET /projects/{project_id}/architecture`

### Domain + traceability (Sprint 3.1 — ATLAS-031)

- `POST /projects/{project_id}/domains/analyze` (Editor+)
- `GET /projects/{project_id}/domains`
- `GET /projects/{project_id}/domains/versions`
- `GET /projects/{project_id}/domains/{analysis_id}`
- `GET /projects/{project_id}/traceability` (`?analysis_id=` optional)

## Target surface (remaining Sprint 3.2+)

### Architecture (Sprint 3.2 migration from MVP singular paths)
- `POST /projects/{project_id}/architectures/generate`
- `GET /projects/{project_id}/architectures`
- `GET /projects/{project_id}/architectures/{id}`
- `POST /projects/{project_id}/architectures/{id}/review`
- `POST /projects/{project_id}/architectures/{id}/approve`

### Risks / assumptions
- `GET /projects/{project_id}/risks`
- `GET /projects/{project_id}/assumptions`

### BOM
- `POST /projects/{project_id}/bom/import`
- `POST /projects/{project_id}/bom/validate`
- `GET /projects/{project_id}/bom/{id}/validation`

### Vendor (global)
- `POST /vendors/catalogue/import`
- `GET /vendors/catalogue/search`
