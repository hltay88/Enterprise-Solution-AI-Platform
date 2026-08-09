# Requirement Traceability

## Purpose
Ensure every proposed architecture component can be traced back to requirements.

## Traceability chain
RKM Requirement
→ Solution Domain
→ Architecture Component
→ Design Decision
→ Vendor/Product Option

## Traceability record
- requirement_id
- domain_id
- architecture_id
- component_id
- decision_id
- evidence
- status

## Status
- Covered
- Partially Covered
- Not Covered
- Conflict
- Optional

## Gate
A recommended architecture cannot be marked Complete if Critical requirements are uncovered.

## Implementation status

**Sprint 3.1 (live):** requirement → solution domain rows in `requirement_traceability`,
built during domain analyze and exposed via `GET /api/v1/projects/{id}/traceability`
(and nested on the domain analysis payload / UI).

**Sprint 3.2 Task 10 (live):** architecture generate appends requirement → domain →
architecture/component rows (same `analysis_id` pin) via
`architecture_traceability.py` + `ArchitectureOptionRepository.add_traceability_rows`.
**Sprint 3.3 (live):** optional `product_id` on traceability rows; Approver Complete
hard-fails when critical/high requirements remain `not_covered` (ATLAS-036).
