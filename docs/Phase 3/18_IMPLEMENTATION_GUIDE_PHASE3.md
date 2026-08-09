# Implementation Guide Phase 3

## Recommended build order

### Sprint 3.0 — Design lock (complete)

Frozen in [`21_PHASE3_DECISIONS.md`](./21_PHASE3_DECISIONS.md):

- **ATLAS-031** — APIs under `/api/v1/projects/{id}/…`
- **ATLAS-032** — Normalized tables; reuse `projects` (no `solution_projects`)
- **ATLAS-033** — Decision IDs ATLAS-031+
- **ATLAS-034** — Keep architecture MVP; refactor in 3.2

No feature code in Sprint 3.0.

### Sprint 3.1 — complete
1. ~~Solution domain model~~
2. ~~Domain identification~~
3. ~~Knowledge pack integration~~
4. ~~Requirement traceability~~ (domain stage)

Shipped surface: catalog/packs, normalized tables, AI identify, analyze service,
`/domains` + `/traceability` APIs, `SolutionDomainPanel`. See [23_PHASE3_CHANGELOG.md](./23_PHASE3_CHANGELOG.md).

Verify: `python3 scripts/verify_sprint_3_1.py` (backend up; rebuild Docker after backend changes).

### Sprint 3.2 — in progress
5. ~~Architecture pattern library~~ (Task 1 — catalog freeze)
6. Candidate architecture generation (refactor MVP → normalized `/architectures`)
7. Capacity planning
8. Architecture scoring
9. Risk and assumption engine

### Sprint 3.3
10. Vendor catalogue
11. Vendor/product mapping
12. BOM import
13. BOM validation
14. Architecture review and approval
15. Phase 3 acceptance

## Engineering rule
Implement one bounded task at a time.

Do not build Proposal, PPT, SOW, or final commercial generation in Phase 3.
