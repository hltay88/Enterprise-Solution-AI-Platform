# Vendor Catalogue Standard

## Purpose
Define how vendor/product data is ingested and used.

## Product record
- vendor
- product_family
- product_model
- category
- capabilities
- specifications
- licensing
- lifecycle_status
- source
- source_date
- region
- confidence

## Source priority
1. Official vendor documentation
2. Authorized distributor data
3. Approved internal catalogue
4. Other sources only when explicitly marked

## Rules
Never invent SKU specifications.

Stale catalogue data must be flagged.

Regional availability must be treated separately from technical compatibility.

## Implementation status

**Sprint 3.3 Tasks 3–4 + 11 (live):** `VendorCatalogueService` +
`POST/GET /api/v1/vendors/catalogue…` (import, seed, search, get). Import/seed
require Editor+. Products with `source_date` older than 365 days are flagged
`is_stale` unless already marked. Seed pack:
`knowledge/phase3/vendors/seed_catalogue.json` (fictional reference vendors only).
UI: **Seed catalogue** on `BomValidationPanel`.
