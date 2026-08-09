# API Phase 3

Base: `/api/v1`  
**Lock (ATLAS-031):** Phase 3 routes are project-scoped under `/projects/{project_id}/…` (except global vendor catalogue).

## Implemented (MVP — ATLAS-034)

Architecture recommendation (Published RKM only):

- `POST /projects/{project_id}/architecture/generate`
- `GET /projects/{project_id}/architecture`

## Target surface (Sprint 3.1+)

### Domain
- `POST /projects/{project_id}/domains/analyze`
- `GET /projects/{project_id}/domains`

### Architecture (Sprint 3.2 migration from MVP singular paths)
- `POST /projects/{project_id}/architectures/generate`
- `GET /projects/{project_id}/architectures`
- `GET /projects/{project_id}/architectures/{id}`
- `POST /projects/{project_id}/architectures/{id}/review`
- `POST /projects/{project_id}/architectures/{id}/approve`

### Traceability
- `GET /projects/{project_id}/traceability`

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
