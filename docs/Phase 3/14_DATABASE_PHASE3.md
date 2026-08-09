# Database Phase 3

**Lock (ATLAS-032):** Reuse existing `projects`. Persist Phase 3 objects in normalized tables. Do not create `solution_projects`.

## Project anchor

- `projects` — existing Phase 1/2 project (solution scope)

## Core entities (target)

| Entity | Sprint | Status | Notes |
|--------|--------|--------|--------|
| `domain_analyses` | 3.1 | **Live** | Versioned domain identification run |
| `solution_domains` | 3.1 | **Live** | Domains for an analysis |
| `domain_requirement_links` | 3.1 | **Live** | Domain ↔ RKM requirement_id |
| `domain_dependencies` | 3.1 | **Live** | Domain → domain_code dependencies |
| `domain_open_questions` | 3.1 | **Live** | Missing info affecting selection |
| `requirement_traceability` | 3.1–3.3 | **Live** | RKM → domain → architecture/component (+ optional `product_id`) |
| `architecture_options` | 3.2 | **Live** | Replaces long-term use of MVP blob |
| `architecture_components` | 3.2 | **Live** | |
| `architecture_relationships` | 3.2 | **Live** | |
| `design_decisions` | 3.2 | **Live** | |
| `architecture_assumptions` | 3.2 | **Live** | |
| `solution_risks` | 3.2 | **Live** | |
| `solution_scores` | 3.2 | **Live** | |
| `capacity_notes` | 3.2 | **Live** | Structured sizing; open_question when inputs missing |
| `vendor_catalogues` | 3.3 | **Live** | Versioned import batches (ATLAS-038) |
| `vendor_products` | 3.3 | **Live** | Source + date + stale flag |
| `product_capabilities` | 3.3 | **Live** | Capability codes for mapping |
| `architecture_product_mappings` | 3.3 | **Live** | Component → product (explicit map) |
| `bom_imports` | 3.3 | **Live** | Immutable imports (ATLAS-039) |
| `bom_items` | 3.3 | **Live** | |
| `bom_validation_results` | 3.3 | **Live** | Separate from import |

## Sprint 3.1 schema (implemented)

Init: `docker/postgres/init/07_phase3_domains.sql`  
Additive mirror: `backend/app/db/schema.py` (`ensure_schema`)  
ORM: `backend/app/models/domain_analysis.py`  
Repository: `backend/app/repositories/domain_repository.py`

## Sprint 3.2 schema (implemented — Task 2)

Init: `docker/postgres/init/08_phase3_architectures.sql`  
Additive mirror: `backend/app/db/schema.py` (`ensure_schema`)  
ORM: `backend/app/models/architecture_option.py`  
Repository: `backend/app/repositories/architecture_option_repository.py`

### Notes

- `requirement_id` columns are **TEXT** (RKM payload identifiers), not FK to `requirements.id`.
- `requirement_traceability.architecture_id` / `component_id` / `decision_id` now FK to
  `architecture_options` / `architecture_components` / `design_decisions` (ON DELETE SET NULL).
- `domain_analyses.knowledge_pack_version` and `architecture_options.knowledge_pack_version`
  store `knowledge/phase3/VERSION` for auditability.
- System of record for candidates is `architecture_options` (+ children). Do not expand
  `architecture_models.payload_json` as the long-term model (ATLAS-034).

## Sprint 3.3 schema (implemented — Task 1)

Init: `docker/postgres/init/09_phase3_vendors_bom.sql`  
Additive mirror: `backend/app/db/schema.py` (`ensure_schema`)  
ORM: `backend/app/models/vendor_bom.py` (+ review/approve columns on `architecture_options`,
`requirement_traceability.product_id`)

### Notes

- Catalogue is **global** (not project-scoped); mappings/BOM are project-scoped.
- Never invent SKU specs in services (ATLAS-035/038) — schema stores source + `is_stale`.
- BOM import rows are immutable; validation writes `bom_validation_results`.
- Architecture Complete gate uses `reviewed_*` / `approved_*` columns
  (`ArchitectureReviewService`; status `complete` when uncovered critical/high = 0).

## Transitional MVP

- `architecture_models` — legacy thin generate/get store (`payload_json`). Retained for
  compatibility; Sprint 3.2 generate/list/detail use normalized tables. Do not grow the blob.

## Rules

- Published RKM remains immutable.
- Architecture / domain versions reference a specific RKM version (`rkm_id`, `rkm_version_label`).
- Vendor catalogue records retain source and timestamp.
- Imported BOMs remain immutable; validation creates a result record.
