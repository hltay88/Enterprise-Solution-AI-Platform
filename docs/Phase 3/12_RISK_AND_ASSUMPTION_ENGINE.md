# Risk and Assumption Engine

## Purpose
Identify risks and assumptions introduced during solution design.

## Risk categories
- Technical
- Security
- Integration
- Capacity
- Availability
- Operational
- Vendor
- Lifecycle
- Commercial
- Implementation

## Risk record
- risk_id
- description
- cause
- impact
- probability
- severity
- mitigation
- owner
- related_requirement

## Assumption record
- assumption_id
- statement
- reason
- affected_components
- validation_required
- status

## Rule
An assumption must never silently become a requirement.

## Implementation status

**Sprint 3.2 Task 8 (live):** `architecture_risks.py` normalizes and merges
risks/assumptions on generate; exposed on candidate detail and
`GET …/risks` / `GET …/assumptions`.
