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
Decision / vendor links remain for later sprints. Approve gate on uncovered criticals
stays Sprint 3.3.
