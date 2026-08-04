# Phase 2 — Atlas Foundation 0.2

**Codename:** Requirement Intelligence Engine  
**Status:** Spec synced from Notion (Not started in code)  
**Source:** [Enterprise Solution AI Platform — Master Index](https://app.notion.com/p/4f7d6a366c264b5092601053e5276325)

Phase 2 transforms customer documents into a versioned, human-approved **Requirement Knowledge Model (RKM)** — the single source of truth for all downstream engines. Architecture, proposals, SOW, BOM, and vendor recommendations are **out of scope** (Phase 3+).

## Read order

1. [PHASE2_PROJECT.md](./PHASE2_PROJECT.md) — objectives and boundaries
2. [TASKS_PHASE2.md](./TASKS_PHASE2.md) — Sprint 2.1 / 2.2 / 2.3
3. [REQUIREMENT_KNOWLEDGE_MODEL.md](./REQUIREMENT_KNOWLEDGE_MODEL.md) — core concept
4. [RKM_SCHEMA.md](./RKM_SCHEMA.md) — canonical schema
5. [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) — build steps
6. [PHASE2_ACCEPTANCE.md](./PHASE2_ACCEPTANCE.md) — exit criteria

## Document index

| File | Topic |
|------|-------|
| [PHASE2_PROJECT.md](./PHASE2_PROJECT.md) | Executive summary |
| [TASKS_PHASE2.md](./TASKS_PHASE2.md) | Sprint tasks |
| [REQUIREMENT_KNOWLEDGE_MODEL.md](./REQUIREMENT_KNOWLEDGE_MODEL.md) | RKM definition |
| [RKM_SCHEMA.md](./RKM_SCHEMA.md) | RKM JSON schema |
| [REQUIREMENT_CLASSIFICATION.md](./REQUIREMENT_CLASSIFICATION.md) | Categories |
| [REQUIREMENT_SCORING.md](./REQUIREMENT_SCORING.md) | Completeness / confidence |
| [CLARIFICATION_ENGINE.md](./CLARIFICATION_ENGINE.md) | Gap analysis questions |
| [OCR_ENGINE.md](./OCR_ENGINE.md) | OCR pipeline |
| [FILE_PROCESSING.md](./FILE_PROCESSING.md) | Upload / storage / evidence |
| [AI_ANALYSIS_STANDARD.md](./AI_ANALYSIS_STANDARD.md) | AI workflow rules |
| [AI_PROMPTS.md](./AI_PROMPTS.md) | Prompt library |
| [PROMPT_STANDARD.md](./PROMPT_STANDARD.md) | Prompt governance |
| [API_PHASE2.md](./API_PHASE2.md) | Phase 2 API endpoints |
| [DATABASE_PHASE2.md](./DATABASE_PHASE2.md) | Database design |
| [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) | Incremental build guide |
| [UI_FLOW.md](./UI_FLOW.md) | Screens and user journey |
| [VERSIONING.md](./VERSIONING.md) | RKM version control |
| [SECURITY_PHASE2.md](./SECURITY_PHASE2.md) | Security standards |
| [ERROR_HANDLING.md](./ERROR_HANDLING.md) | Error strategy |
| [TEST_PLAN_PHASE2.md](./TEST_PLAN_PHASE2.md) | Testing strategy |
| [KNOWLEDGE_PACK_STANDARD.md](./KNOWLEDGE_PACK_STANDARD.md) | Knowledge library structure |
| [DECISIONS_PHASE2.md](./DECISIONS_PHASE2.md) | Architecture decisions |
| [CHANGELOG_PHASE2.md](./CHANGELOG_PHASE2.md) | Version changelog |
| [PHASE2_ACCEPTANCE.md](./PHASE2_ACCEPTANCE.md) | Exit criteria |
| [PHASE3_HANDOVER.md](./PHASE3_HANDOVER.md) | Handover to Architecture Engine |

## Note on decision IDs

`DECISIONS_PHASE2.md` uses Decision 011–016 for RKM rules. The Sprint 1 log in `docs/DECISIONS.md` already uses ATLAS-011…015a for other topics. Renumber before merging Phase 2 decisions into the main decision log (suggested: ATLAS-020+).
