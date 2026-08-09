# UI Flow Phase 3

## Workflow
Project
→ Published RKM
→ Solution Domains
→ Architecture Options
→ Compare Architectures
→ Traceability
→ Risks & Assumptions
→ Vendor Mapping
→ BOM Validation
→ Architecture Review
→ Approval

## Implemented (Sprint 3.1)

On the project page, after RKM governance and **before** Architecture:

- **Solution domain model** (`SolutionDomainPanel`) — Analyze domains from Published RKM;
  review domains, confidence, dependencies, open questions, and requirement→domain
  traceability (domain stage of the chain).

Architecture recommendation panel remains the thin MVP (ATLAS-034) until Sprint 3.2.

## Main screens
- Solution Overview
- Domain Map — **partial (3.1 panel on project page)**
- Architecture Designer — MVP generate/get only
- Architecture Comparison
- Requirement Traceability — **partial (domain stage in Domain panel)**
- Capacity Calculator
- Risks & Assumptions
- Vendor Comparison
- BOM Validation
- Architecture Approval

## UX principle
Show why the AI made a recommendation.

Users must be able to inspect:
- source requirement
- evidence
- design rule
- architecture component
- vendor mapping
- confidence
