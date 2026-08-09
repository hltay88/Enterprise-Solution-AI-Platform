# Phase 3 Changelog

## 0.3.0 (baseline pack + thin architecture MVP)

Doc pack `01`–`23` added under `docs/Phase 3/`.

**Shipped in code (MVP slice):**
- Architecture recommendation from Published RKM only (ATLAS-023)
- `architecture_models` persistence + generate/get APIs under `/api/v1/projects/{id}/architecture`
- Architecture panel in the project UI
- Vendor-neutral technology categories (no product SKUs)

**Still planned (see backlog / acceptance):** domain identification APIs, pattern library,
capacity, scoring, risks/assumptions, vendor catalogue, BOM import/validation,
architecture review/approve under the `/solutions/…` surface in `15_API_PHASE3.md`.

## Revision policy
Do not silently alter the Phase 3 baseline.

Record architectural changes here and in the relevant ADR.
