# Phase 3 Changelog

## 0.3.1-task2 (domain schema)

Sprint 3.1 Task 2: `domain_analyses`, `solution_domains`, links/dependencies/open questions,
and `requirement_traceability` via `07_phase3_domains.sql` + `ensure_schema` + ORM models.
No domain analyze service/API yet.

## 0.3.1-task1 (domain catalog freeze)

Sprint 3.1 Task 1: frozen Phase 3 domain codes in `knowledge/phase3/domains/catalog.json`,
`knowledge/phase3/VERSION`, priority domain overview stubs, and loader
`backend/app/services/phase3_domain_catalog.py`. No domain analyze API yet.

## 0.3.0-sprint3.0 (design lock)

Sprint 3.0 accepted ATLAS-031…034 (and mapped former ADR-017…024 → ATLAS-035…041).
API/DB/MVP fate frozen in `21_PHASE3_DECISIONS.md`. No feature code in this revision.

## 0.3.0 (baseline pack + thin architecture MVP)

Doc pack `01`–`23` added under `docs/Phase 3/`.

**Shipped in code (MVP slice):**
- Architecture recommendation from Published RKM only (ATLAS-023)
- `architecture_models` persistence + generate/get APIs under `/api/v1/projects/{id}/architecture`
- Architecture panel in the project UI
- Vendor-neutral technology categories (no product SKUs)

**Still planned (see backlog / acceptance):** domain identification, pattern library,
capacity, scoring, risks/assumptions, vendor catalogue, BOM import/validation,
architecture review/approve under the locked `/projects/{id}/…` surface in `15_API_PHASE3.md`.

## Revision policy
Do not silently alter the Phase 3 baseline.

Record architectural changes here and in the relevant ADR.
