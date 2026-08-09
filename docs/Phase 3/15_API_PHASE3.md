# API Phase 3

Base: `/api/v1`  
**Lock (ATLAS-031):** Phase 3 routes are project-scoped under `/projects/{project_id}/…`
(except the global vendor catalogue).

Auth: JWT as Phase 2. Analyze/generate/import/map/review/validate require Editor+;
approve/Complete require Approver. Reads require authenticated project owner.
Envelope: ATLAS-014 `success_response`. No `/solutions/` routes.

## Domain + traceability (Sprint 3.1) — **Live**

- `POST /projects/{project_id}/domains/analyze` (Editor+)
- `GET /projects/{project_id}/domains`
- `GET /projects/{project_id}/domains/versions`
- `GET /projects/{project_id}/domains/{analysis_id}`
- `GET /projects/{project_id}/traceability` (`?analysis_id=` optional)

## Architecture candidates (Sprint 3.2) — **Live**

- `POST /projects/{project_id}/architectures/generate` (Editor+; Published RKM + latest domains)
- `GET /projects/{project_id}/architectures`
- `GET /projects/{project_id}/architectures/{architecture_id}`
- `GET /projects/{project_id}/risks` (`?architecture_id=` optional; default = latest generation)
- `GET /projects/{project_id}/assumptions` (`?architecture_id=` optional)

**MVP singular aliases (deprecated, kept through 3.3):**

- `POST /projects/{project_id}/architecture/generate` → plural generate
- `GET /projects/{project_id}/architecture` → latest option

## Vendor catalogue (Sprint 3.3) — **Live**

Global (not project-scoped). Never invents SKU specs; `source_date` older than 365 days → `is_stale`.
Seed: `knowledge/phase3/vendors/seed_catalogue.json` (fictional vendors only).

- `POST /vendors/catalogue/import` (Editor+)
- `POST /vendors/catalogue/seed` (Editor+; idempotent; `?force=true` re-imports)
- `GET /vendors/catalogue/search` (`q`, `vendor`, `category`, `region`, `catalogue_id`, `include_stale`, `limit`)
- `GET /vendors/catalogue/{catalogue_id}`

## Product mapping (Sprint 3.3) — **Live**

Explicit Map products (ATLAS-035) — not run on architecture generate.

- `POST /projects/{project_id}/architectures/{architecture_id}/map-products` (Editor+)
- `GET /projects/{project_id}/architectures/{architecture_id}/product-mappings`
- `PATCH /projects/{project_id}/product-mappings/{mapping_id}` (Editor+; status/preference)

Optional map body: `component_ids`, `catalogue_id`, `region`, `include_stale`.

## BOM import & validation (Sprint 3.3) — **Live**

Imports are immutable evidence (ATLAS-039). Validation appends `bom_validation_results`.

- `POST /projects/{project_id}/bom/import` (Editor+)
- `GET /projects/{project_id}/bom`
- `GET /projects/{project_id}/bom/{bom_import_id}`
- `POST /projects/{project_id}/bom/{bom_import_id}/validate` (Editor+)
- `GET /projects/{project_id}/bom/{bom_import_id}/validation`

Import body: `source` (required), optional `source_filename` / `architecture_id` / `notes`,
and `items[]` with `product_model` | `sku` | `description`. Exact catalogue vendor+model
matches set `mapped_product_id`.

Validate optional body: `architecture_id`, `catalogue_id`. Status:
`passed` | `needs_review` | `failed`. Uncertain items set `requires_human_validation`.

## Architecture review & Complete (Sprint 3.3) — **Live**

- `POST /projects/{project_id}/architectures/{architecture_id}/review` (Editor+)
- `POST /projects/{project_id}/architectures/{architecture_id}/approve` (Approver)

Review sets `under_review` + `reviewed_*` and returns soft `uncovered_critical_count`.
Approve requires prior `under_review`, sets `complete` + `approved_*`, and **hard-fails (422)**
if any critical/high requirements remain uncovered (ATLAS-036/037).

DTO contracts: `backend/app/schemas/vendor_bom.py`, `architecture_option.py`.
