# API Phase 3

Base: `/api/v1`  
**Lock (ATLAS-031):** Phase 3 routes are project-scoped under `/projects/{project_id}/…` (except global vendor catalogue).

## Implemented

### Architecture candidates (Sprint 3.2 — ATLAS-031 / ATLAS-034) — **Live**

- `POST /projects/{project_id}/architectures/generate` (Editor+; Published RKM + latest domains)
- `GET /projects/{project_id}/architectures`
- `GET /projects/{project_id}/architectures/{architecture_id}`
- `GET /projects/{project_id}/risks` (`?architecture_id=` optional; default = latest generation)
- `GET /projects/{project_id}/assumptions` (`?architecture_id=` optional)

**MVP singular aliases (deprecated, kept through 3.2):**

- `POST /projects/{project_id}/architecture/generate` → plural generate
- `GET /projects/{project_id}/architecture` → latest option

Review/approve stay Sprint 3.3.

### Domain + traceability (Sprint 3.1 — ATLAS-031)

- `POST /projects/{project_id}/domains/analyze` (Editor+)
- `GET /projects/{project_id}/domains`
- `GET /projects/{project_id}/domains/versions`
- `GET /projects/{project_id}/domains/{analysis_id}`
- `GET /projects/{project_id}/traceability` (`?analysis_id=` optional)

Auth: JWT as Phase 2. Generate/analyze require Editor+; reads require authenticated project owner.
Envelope: ATLAS-014 `success_response`. No `/solutions/` routes.

## Implemented (Sprint 3.3 partial)

### Vendor catalogue (Task 3 — ATLAS-038) — **Live**

Global (not project-scoped):

- `POST /vendors/catalogue/import` (Editor+)
- `GET /vendors/catalogue/search` (`q`, `vendor`, `category`, `region`, `catalogue_id`, `include_stale`, `limit`)
- `GET /vendors/catalogue/{catalogue_id}`

Never invents SKU specs; products older than 365 days (by `source_date`) are flagged `is_stale`.

## Target surface (Sprint 3.3 remaining)

DTO contracts in `backend/app/schemas/vendor_bom.py`.

### Architecture review / approve
- `POST /projects/{project_id}/architectures/{id}/review`
- `POST /projects/{project_id}/architectures/{id}/approve`

### Product mapping
- `POST /projects/{project_id}/architectures/{id}/map-products` (explicit action)
- `GET /projects/{project_id}/architectures/{id}/product-mappings`

### BOM
- `POST /projects/{project_id}/bom/import`
- `POST /projects/{project_id}/bom/{id}/validate`
- `GET /projects/{project_id}/bom/{id}/validation`
