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
| `requirement_traceability` | 3.1 | **Live** | RKM → domain (+ nullable later stages) |
| `architecture_options` | 3.2 | **Live** | Replaces long-term use of MVP blob |
| `architecture_components` | 3.2 | **Live** | |
| `architecture_relationships` | 3.2 | **Live** | |
| `design_decisions` | 3.2 | **Live** | |
| `architecture_assumptions` | 3.2 | **Live** | |
| `solution_risks` | 3.2 | **Live** | |
| `solution_scores` | 3.2 | **Live** | |
| `capacity_notes` | 3.2 | **Live** | Structured sizing; open_question when inputs missing |
| `vendor_catalogues` | 3.3 | Planned | |
| `vendor_products` | 3.3 | Planned | |
| `product_capabilities` | 3.3 | Planned | |
| `bom_imports` | 3.3 | Planned | Immutable imports |
| `bom_items` | 3.3 | Planned | |
| `bom_validation_results` | 3.3 | Planned | Separate from import |

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
- `architecture_models` remains as transitional MVP store until generate cutover (ATLAS-034).

## Transitional MVP

- `architecture_models` — thin generate/get store (`payload_json`). Kept until Sprint 3.2 refactor (ATLAS-034). New 3.1 tables must not depend on expanding this JSON as the system of record.

## Rules

- Published RKM remains immutable.
- Architecture / domain versions reference a specific RKM version (`rkm_id`, `rkm_version_label`).
- Vendor catalogue records retain source and timestamp.
- Imported BOMs remain immutable; validation creates a result record.
