# BOM Intelligence

## Purpose
Support solution component mapping and validate vendor/distributor BOMs.

## Phase 3 scope
- Define required component categories.
- Map architecture components to candidate products.
- Import external BOMs.
- Detect missing components.
- Detect duplicate components.
- Detect obvious incompatibilities.
- Compare BOM against requirements.

## Not in scope
- Final commercial quotation
- Purchase order
- Automatic vendor negotiation

## BOM validation
Check:
- quantity
- model
- licence
- subscription
- compatibility
- dependencies
- power
- optics/transceivers
- support
- required accessories

## Rule
If product information is uncertain, flag it for human validation.

## Implementation status

**Sprint 3.3 Tasks 7–8 + 11 (live):** immutable `POST …/bom/import`, append-only
`POST …/bom/{id}/validate` / `GET …/validation`, heuristics in `bom_validation.py`
(missing/duplicate/unknown/compat/uncertain + companion flags). UI:
`BomValidationPanel` (seed catalogue, import lines, validate).
