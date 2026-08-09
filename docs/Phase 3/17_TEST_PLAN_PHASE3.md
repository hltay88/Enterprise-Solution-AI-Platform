# Test Plan Phase 3

## Unit tests
- Domain identification
- Architecture scoring
- Capacity calculations
- Traceability
- Risk generation
- BOM validation

## Integration tests
RKM → Domain Engine
Domain Engine → Architecture Engine
Architecture → Vendor Mapping
Architecture → BOM Validation

## Golden datasets
Create representative projects for:
- Campus network
- Wi-Fi
- Cybersecurity
- Data Centre
- Cloud
- AV / LED
- Digital signage
- Smart building

## Acceptance criteria
- No critical requirement is silently omitted.
- Every component has traceability.
- Unsupported product claims are rejected.
- Version references are correct.
- Human approval is enforced.

## Regression
Maintain a fixed golden set and run it after prompt/model changes.
