# Architecture Recommendation Engine

## Purpose
Generate candidate solution architectures from a published RKM.

## Workflow
Published RKM
→ Domain identification
→ Architecture patterns
→ Candidate architectures
→ Constraint validation
→ Requirement traceability
→ Risk analysis
→ Scoring
→ Recommended architecture

## Candidate generation
At least one architecture is required.
Where meaningful, generate alternatives such as:
- Standard
- High availability
- Cloud-managed
- Hybrid
- Vendor-neutral reference

## Recommendation output
- architecture_id
- title
- summary
- components
- topology
- dependencies
- requirements_covered
- assumptions
- risks
- advantages
- disadvantages
- confidence
- score

## Human control
AI recommendations remain Draft until reviewed.

## Implementation status

**Sprint 3.2 (live):** `ArchitectureGenerationService` + plural `/architectures` APIs
persist candidates on normalized tables with capacity notes, risks/assumptions,
scores, and architecture-stage traceability. UI: `ArchitecturePanel` (reviewable
candidates; no approve). Singular `/architecture` routes are deprecated aliases.
