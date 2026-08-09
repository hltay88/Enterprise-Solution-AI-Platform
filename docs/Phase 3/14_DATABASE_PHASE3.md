# Database Phase 3

**Lock (ATLAS-032):** Reuse existing `projects`. Persist Phase 3 objects in normalized tables. Do not create `solution_projects`.

## Project anchor

- `projects` — existing Phase 1/2 project (solution scope)

## Core entities (target)

| Entity | Sprint | Notes |
|--------|--------|--------|
| `solution_domains` | 3.1 | Domain identification output |
| `requirement_traceability` | 3.1 | RKM → domain → component chain |
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

## Transitional MVP

- `architecture_models` — thin generate/get store (`payload_json`). Kept until Sprint 3.2 refactor (ATLAS-034). New 3.1 tables must not depend on expanding this JSON as the system of record.

## Rules

- Published RKM remains immutable.
- Architecture / domain versions reference a specific RKM version (`rkm_id`, `rkm_version_label`).
- Vendor catalogue records retain source and timestamp.
- Imported BOMs remain immutable; validation creates a result record.
