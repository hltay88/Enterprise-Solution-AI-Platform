# API Phase 3

Base: /api/v1

## Implemented (MVP)

Architecture recommendation (Published RKM only):

- `POST /projects/{projectId}/architecture/generate`
- `GET /projects/{projectId}/architecture`

## Target surface (not all shipped)

### Domain
POST /solutions/{projectId}/domains/analyze
GET /solutions/{projectId}/domains

### Architecture
POST /solutions/{projectId}/architectures/generate
GET /solutions/{projectId}/architectures
GET /solutions/{projectId}/architectures/{id}
POST /solutions/{projectId}/architectures/{id}/review
POST /solutions/{projectId}/architectures/{id}/approve

### Traceability
GET /solutions/{projectId}/traceability

### Vendor
POST /vendors/catalogue/import
GET /vendors/catalogue/search

### BOM
POST /solutions/{projectId}/bom/import
POST /solutions/{projectId}/bom/validate
GET /solutions/{projectId}/bom/{id}/validation

### Risks
GET /solutions/{projectId}/risks
GET /solutions/{projectId}/assumptions
