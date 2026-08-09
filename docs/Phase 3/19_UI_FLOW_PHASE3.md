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

## Implemented (Sprint 3.2 Task 12)

- **Architecture candidates** (`ArchitecturePanel`) — Generate/list/select candidates from
  Published RKM + latest domains; inspect components, scores, risks, assumptions, capacity
  notes, and pattern/RKM/domain pins. No approve UI yet (3.3).

## Main screens
- Solution Overview
- Domain Map — **partial (3.1 panel on project page)**
- Architecture Designer — **candidates panel (3.2)**; compare/approve later
- Architecture Comparison
- Requirement Traceability — **partial (domain stage in Domain panel; arch links via API)**
- Capacity Calculator — **partial (capacity notes on candidate)**
- Risks & Assumptions — **partial (on candidate + `/risks` `/assumptions` APIs)**
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
