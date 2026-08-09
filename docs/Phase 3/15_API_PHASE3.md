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
- `POST /vendors/catalogue/seed` (Editor+; idempotent Atlas seed pack; `?force=true` re-imports)
- `GET /vendors/catalogue/search` (`q`, `vendor`, `category`, `region`, `catalogue_id`, `include_stale`, `limit`)
- `GET /vendors/catalogue/{catalogue_id}`

Never invents SKU specs; products older than 365 days (by `source_date`) are flagged `is_stale`.
Seed file: `knowledge/phase3/vendors/seed_catalogue.json` (fictional vendors only).

### Product mapping (Task 6 — ATLAS-035) — **Live**

- `POST /projects/{project_id}/architectures/{architecture_id}/map-products` (Editor+; explicit)
- `GET /projects/{project_id}/architectures/{architecture_id}/product-mappings`
- `PATCH /projects/{project_id}/product-mappings/{mapping_id}` (Editor+; status/preference)

Optional body on map: `component_ids`, `catalogue_id`, `region`, `include_stale`.

## BOM import (Sprint 3.3 Task 7)

Immutable evidence snapshot (ATLAS-039). Editor+ for import; any project member
for list/get.

- `POST /projects/{project_id}/bom/import` (Editor+)
- `GET /projects/{project_id}/bom`
- `GET /projects/{project_id}/bom/{bom_import_id}`

Body: `source` (required), optional `source_filename` / `architecture_id` /
`notes`, and `items[]` with `product_model` | `sku` | `description`. Exact
catalogue vendor+model matches set `mapped_product_id`; inventing SKUs is
forbidden.

## Target surface (Sprint 3.3 remaining)

DTO contracts in `backend/app/schemas/vendor_bom.py`.

## Architecture review (Sprint 3.3 Task 9)

Human review of an AI candidate (ATLAS-037). Editor+. Does **not** approve.

- `POST /projects/{project_id}/architectures/{architecture_id}/review`

Optional body: `{ "note": "..." }`. Sets status `under_review` and
`reviewed_at` / `reviewed_by` / `review_note`. Response includes soft
`uncovered_critical_count` (informational; hard Complete gate is approve Task 10).
Blocked once status is `approved` or `complete`.

### Architecture approve (Task 10)
- `POST /projects/{project_id}/architectures/{id}/approve`

## BOM validation (Sprint 3.3 Task 8)

Append-only results (import stays immutable). Editor+ to validate; any member
to read latest result.

- `POST /projects/{project_id}/bom/{bom_import_id}/validate` (Editor+)
- `GET /projects/{project_id}/bom/{bom_import_id}/validation`

Optional body: `architecture_id`, `catalogue_id`. Status:
`passed` | `needs_review` | `failed`. Issues include missing/duplicate/
unknown_model/compatibility/uncertain_spec and companion flags; uncertain
items set `requires_human_validation` (ATLAS-039).
