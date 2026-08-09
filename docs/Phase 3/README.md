# Phase 3 — Solution Recommendation Engine

**Folder:** `docs/Phase 3/` (canonical for Phase 3)  
**Codename:** Solution Recommendation Engine (Atlas Foundation 0.3)  
**Input rule (ATLAS-023):** Consume only **Published** RKMs — never raw customer documents.  
**Sprint 3.0 locks:** [21_PHASE3_DECISIONS.md](./21_PHASE3_DECISIONS.md) (ATLAS-031…034) — complete.  
**Sprint 3.1:** Solution Domain Identification — implemented (catalog → analyze API → UI).

## Read order

1. [01_PHASE3_PROJECT.md](./01_PHASE3_PROJECT.md) — purpose and boundaries  
2. [02_SOLUTION_DOMAIN_MODEL.md](./02_SOLUTION_DOMAIN_MODEL.md)  
3. [03_SOLUTION_ARCHITECTURE_STANDARD.md](./03_SOLUTION_ARCHITECTURE_STANDARD.md)  
4. [04_ARCHITECTURE_ENGINE.md](./04_ARCHITECTURE_ENGINE.md)  
5. [18_IMPLEMENTATION_GUIDE_PHASE3.md](./18_IMPLEMENTATION_GUIDE_PHASE3.md) — build order  
6. [22_PHASE3_TASK_BACKLOG.md](./22_PHASE3_TASK_BACKLOG.md)  
7. [20_PHASE3_ACCEPTANCE_AND_HANDOVER.md](./20_PHASE3_ACCEPTANCE_AND_HANDOVER.md)  

Handover context from Phase 2: [../Phase 2/PHASE3_HANDOVER.md](../Phase%202/PHASE3_HANDOVER.md)

## Document index

| File | Topic |
|------|-------|
| [01_PHASE3_PROJECT.md](./01_PHASE3_PROJECT.md) | Executive summary |
| [02_SOLUTION_DOMAIN_MODEL.md](./02_SOLUTION_DOMAIN_MODEL.md) | Domain model |
| [03_SOLUTION_ARCHITECTURE_STANDARD.md](./03_SOLUTION_ARCHITECTURE_STANDARD.md) | Architecture standard |
| [04_ARCHITECTURE_ENGINE.md](./04_ARCHITECTURE_ENGINE.md) | Architecture engine |
| [05_ARCHITECTURE_PATTERNS.md](./05_ARCHITECTURE_PATTERNS.md) | Pattern library |
| [06_CAPACITY_PLANNING.md](./06_CAPACITY_PLANNING.md) | Capacity |
| [07_REQUIREMENT_TRACEABILITY.md](./07_REQUIREMENT_TRACEABILITY.md) | Traceability |
| [08_VENDOR_NEUTRAL_STANDARD.md](./08_VENDOR_NEUTRAL_STANDARD.md) | Vendor-neutral rules |
| [09_VENDOR_CATALOG_STANDARD.md](./09_VENDOR_CATALOG_STANDARD.md) | Vendor catalogue |
| [10_BOM_INTELLIGENCE.md](./10_BOM_INTELLIGENCE.md) | BOM |
| [11_SOLUTION_SCORING.md](./11_SOLUTION_SCORING.md) | Scoring |
| [12_RISK_AND_ASSUMPTION_ENGINE.md](./12_RISK_AND_ASSUMPTION_ENGINE.md) | Risks / assumptions |
| [13_AI_PROMPTS_PHASE3.md](./13_AI_PROMPTS_PHASE3.md) | Prompts |
| [14_DATABASE_PHASE3.md](./14_DATABASE_PHASE3.md) | Database |
| [15_API_PHASE3.md](./15_API_PHASE3.md) | API |
| [16_SECURITY_PHASE3.md](./16_SECURITY_PHASE3.md) | Security |
| [17_TEST_PLAN_PHASE3.md](./17_TEST_PLAN_PHASE3.md) | Tests |
| [18_IMPLEMENTATION_GUIDE_PHASE3.md](./18_IMPLEMENTATION_GUIDE_PHASE3.md) | Implementation order |
| [19_UI_FLOW_PHASE3.md](./19_UI_FLOW_PHASE3.md) | UI flow |
| [20_PHASE3_ACCEPTANCE_AND_HANDOVER.md](./20_PHASE3_ACCEPTANCE_AND_HANDOVER.md) | Exit / Phase 4 input |
| [21_PHASE3_DECISIONS.md](./21_PHASE3_DECISIONS.md) | ADRs |
| [22_PHASE3_TASK_BACKLOG.md](./22_PHASE3_TASK_BACKLOG.md) | Backlog |
| [23_PHASE3_CHANGELOG.md](./23_PHASE3_CHANGELOG.md) | Changelog |

## Implementation status (codebase)

**Shipped — architecture MVP (ATLAS-034):** generate / fetch architecture recommendation from a
Published RKM (`POST/GET /api/v1/projects/{id}/architecture…`, `architecture_models`, Architecture panel).

**Shipped — Sprint 3.1 domains + domain-stage traceability (ATLAS-031/032):**
- Catalog + packs: `knowledge/phase3/`, `phase3_domain_catalog.py`, `phase3_knowledge_packs.py`
- Schema: `07_phase3_domains.sql` / `ensure_schema` / `domain_analysis` ORM
- Service: `DomainIdentificationService` (+ confidence, enrichment, traceability helpers)
- API: `POST/GET …/domains…`, `GET …/traceability` (see [15_API_PHASE3.md](./15_API_PHASE3.md))
- UI: `SolutionDomainPanel` on the project page (before Architecture)

**Not yet built (Sprint 3.2+):** plural `/architectures` lifecycle, pattern library, capacity,
scoring, risks/assumptions, vendor catalogue, BOM validation, architecture review/approve
(see [15_API_PHASE3.md](./15_API_PHASE3.md), [22_PHASE3_TASK_BACKLOG.md](./22_PHASE3_TASK_BACKLOG.md)).

API namespace remains `/api/v1/projects/{id}/…` — no `/solutions/` surface (ATLAS-031).

**Verify Sprint 3.1:** with Atlas running, `python3 scripts/verify_sprint_3_1.py`
(`--unit-only` / `--smoke-only` supported). Rebuild Docker backend after code changes.
