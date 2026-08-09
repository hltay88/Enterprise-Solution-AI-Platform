# Database Phase 3

**Lock (ATLAS-032):** Reuse existing `projects`. Persist Phase 3 objects in normalized tables. Do not create `solution_projects`.

## Project anchor

- `projects` — existing Phase 1/2 project (solution scope)

## Core entities (target)

| Entity | Sprint | Notes |
|--------|--------|--------|
| `domain_analyses` | 3.1 | Versioned domain identification run (schema Task 2) |
| `solution_domains` | 3.1 | Domains for an analysis |
| `domain_requirement_links` | 3.1 | Domain ↔ RKM requirement_id |
| `domain_dependencies` | 3.1 | Domain → domain_code dependencies |
| `domain_open_questions` | 3.1 | Missing info affecting selection |
| `requirement_traceability` | 3.1 | RKM → domain (+ nullable later stages) |
| `architecture_options` | 3.2 | Replaces long-term use of MVP blob |
| `architecture_components` | 3.2 | |
| `architecture_relationships` | 3.2 | |
| `design_decisions` | 3.2 | |
| `architecture_assumptions` | 3.2 | |
| `solution_risks` | 3.2 | |
| `solution_scores` | 3.2 | |
| `vendor_catalogues` | 3.3 | |
| `vendor_products` | 3.3 | |
| `product_capabilities` | 3.3 | |
| `bom_imports` | 3.3 | Immutable imports |
| `bom_items` | 3.3 | |
| `bom_validation_results` | 3.3 | Separate from import |

## Sprint 3.1 schema

Init: `docker/postgres/init/07_phase3_domains.sql`  
Additive mirror: `backend/app/db/schema.py` (`ensure_schema`)  
ORM: `backend/app/models/domain_analysis.py`

### Notes

- `requirement_id` columns are **TEXT** (RKM payload identifiers), not FK to `requirements.id`.
- `requirement_traceability.architecture_id` / `component_id` / `decision_id` are nullable UUIDs without FK until Sprint 3.2+ entities exist.
- `domain_analyses.knowledge_pack_version` stores `knowledge/phase3/VERSION` for auditability.

## Transitional MVP

- `architecture_models` — thin generate/get store (`payload_json`). Kept until Sprint 3.2 refactor (ATLAS-034). New 3.1 tables must not depend on expanding this JSON as the system of record.

## Rules

- Published RKM remains immutable.
- Architecture / domain versions reference a specific RKM version (`rkm_id`, `rkm_version_label`).
- Vendor catalogue records retain source and timestamp.
- Imported BOMs remain immutable; validation creates a result record.
