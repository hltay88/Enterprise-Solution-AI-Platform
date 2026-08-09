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

### Sprint 3.2 — complete
5. ~~Architecture pattern library~~
6. ~~Candidate architecture generation~~ (normalized `/architectures` + singular aliases)
7. ~~Capacity planning~~ (`capacity_notes` helper; no fabricate)
8. ~~Architecture scoring~~
9. ~~Risk and assumption engine~~
10. ~~Architecture-stage traceability~~
11. ~~Plural APIs + MVP aliases~~
12. ~~Architecture candidates UI~~
13. ~~Docs / backlog / changelog polish~~
14. ~~`scripts/verify_sprint_3_2.py` + regression~~

Shipped surface: pattern catalog, `architecture_options` tree, generation service
(Published RKM + domain gate), capacity/risks/scores/traceability, plural APIs,
`ArchitecturePanel`. Approve remains Sprint 3.3.

Verify: `python3 scripts/verify_sprint_3_2.py` (backend up; rebuild Docker after backend changes).

### Sprint 3.3 — in progress
1. ~~Vendor/BOM/mapping schema + ORM~~ (Task 1)
2. ~~Pydantic schemas~~ (Task 2)
3. ~~Catalogue import + search API~~ (Task 3)
4. ~~Sample catalogue pack~~ (Task 4)
5. ~~Product mapping service~~ (Task 5 — explicit action)
6. ~~Mapping APIs~~ (Task 6)
7. BOM import — Sprint 3.3 Task 7 (`POST …/bom/import`; immutable)
8. BOM validation — Sprint 3.3 Task 8 (`POST …/bom/{id}/validate`)
9. Architecture review — Sprint 3.3 Task 9 (`POST …/architectures/{id}/review`)
10. Architecture approve — Sprint 3.3 Task 10 (hard Complete gate; Approver)
11. Frontend panels — Sprint 3.3 Task 11 (map/review/Complete + BOM panel)
12. Docs polish
13. `scripts/verify_sprint_3_3.py` + acceptance

Defaults: seed + import catalogue; explicit Map products; hard Complete gate;
singular `/architecture` aliases kept deprecated through 3.3.

## Engineering rule
Implement one bounded task at a time.

Do not build Proposal, PPT, SOW, or final commercial generation in Phase 3.
