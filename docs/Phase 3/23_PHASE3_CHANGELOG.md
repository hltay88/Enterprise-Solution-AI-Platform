# Phase 3 Changelog

## 0.3.2-task9 (architecture scoring engine)

Sprint 3.2 Task 9: `architecture_scoring.py` applies default weights from
`11_SOLUTION_SCORING.md`, requires explanations, fills missing dimensions with
explicit heuristic scores, and records overall_score + weight profile on
candidates. Wired into `ArchitectureGenerationService`. Decision support only.

## 0.3.2-task8 (risks and assumptions builder)

Sprint 3.2 Task 8: `architecture_risks.py` normalizes legacy risk/assumption
shapes, merges Published RKM risks, adds baseline unvalidated assumptions
(never silent requirements), and domain starter risks. Wired into
`ArchitectureGenerationService`. Tables already live from Task 2.

## 0.3.2-task7 (capacity notes helper)

Sprint 3.2 Task 7: `architecture_capacity.py` sanitizes fabricated sizing
results into open questions and enriches domain-relevant capacity notes
(no invented numbers). Wired into `ArchitectureGenerationService` before
persist. Aligns with `06_CAPACITY_PLANNING.md`.

## 0.3.2-task6 (architecture generation service)

Sprint 3.2 Task 6: `ArchitectureGenerationService` gates on Published RKM +
latest domain analysis, builds pattern pack context, calls
`recommend_architectures`, persists via `ArchitectureOptionRepository`, and
audits `architectures.generate`. No plural HTTP routes yet (Task 11). MVP
singular `ArchitectureService` unchanged.

## 0.3.2-task5 (architecture candidates AI)

Sprint 3.2 Task 5: `recommend_architectures` on AI providers, prompt
`architecture_candidates.txt`, `normalize_architecture_candidates`, and local
multi-candidate heuristics. MVP singular `recommend_architecture` unchanged.
No generate service/HTTP yet.

## 0.3.2-task4 (architecture option repository)

Sprint 3.2 Task 4: `ArchitectureOptionRepository` with `create_generation_tree`,
version helpers, and read APIs for options/components/risks/scores/capacity.
MVP `ArchitectureRepository` unchanged. No generate HTTP yet.

## 0.3.2-task3 (architecture candidate schemas)

Sprint 3.2 Task 3: Pydantic AI + API contracts in
`backend/app/schemas/architecture_option.py` (multi-candidate extraction,
catalog-bound patterns, capacity no-fabricate, score dimensions). No generate
service/API yet. MVP `schemas/architecture.py` unchanged.

## 0.3.2-task2 (normalized architecture schema)

Sprint 3.2 Task 2: `architecture_options` + components/relationships/decisions,
assumptions, risks, scores, and `capacity_notes` via `08_phase3_architectures.sql`
+ `ensure_schema` + ORM. Traceability FKs wired. No generate service/API yet.

## 0.3.2-task1 (architecture pattern catalog freeze)

Sprint 3.2 Task 1: frozen pattern codes in `knowledge/phase3/patterns/catalog.json`,
pack version bumped to `1.1.0`, priority pattern stubs, and loader
`phase3_pattern_catalog.py`. No architecture generate API yet.

## 0.3.1-task14 (sprint verification)

Sprint 3.1 Task 14: `scripts/verify_sprint_3_1.py` runs pytest + API smoke
(publish RKM → domains/analyze → GET domains/traceability → architecture generate).
Also fixes `DomainRepository.create_analysis_tree` flush order so dependencies
insert after `solution_domains` (FK violation under real DB).

## 0.3.1-task13 (docs polish)

Sprint 3.1 Task 13: aligned Phase 3 docs with shipped domain/traceability work —
API/DB status, backlog P0 domain items checked, README/UI/implementation guide updated.
No `/solutions/` API surface (ATLAS-031).

## 0.3.1 (Sprint 3.1 — Solution Domain Identification)

Shipped end-to-end: frozen catalog + packs, normalized domain tables, AI identify,
`DomainIdentificationService`, `/domains` + `/traceability` APIs, `SolutionDomainPanel`,
plus `scripts/verify_sprint_3_1.py` for unit + smoke regression.

## 0.3.1-task12 (solution domain UI)

Sprint 3.1 Task 12: `SolutionDomainPanel` on the project page (before Architecture)
shows domains, confidence, deps, open questions, and traceability; Analyze action.

## 0.3.1-task11 (domain API routes)

Sprint 3.1 Task 11: `v1_domains.py` exposes analyze/get/versions/traceability under
`/api/v1/projects/{id}/…` (ATLAS-031). Editor+ for analyze; ownership via service.

## 0.3.1-task10 (domain confidence)

Sprint 3.1 Task 10: `domain_confidence.py` normalizes confidence to 0–1 and applies
penalties for thin evidence and selection-affecting open questions.

## 0.3.1-task9 (dependencies & open questions)

Sprint 3.1 Task 9: `domain_enrichment.py` validates catalog dependencies, flags missing
dep domains / cycles, and adds selection-affecting open questions (no fabricated inputs).

## 0.3.1-task8 (requirement→domain traceability)

Sprint 3.1 Task 8: `domain_traceability.py` builds covered/partial/optional/not_covered
rows during analyze; uncovered critical/high counted in audit metadata.

## 0.3.1-task7 (domain identification service)

Sprint 3.1 Task 7: `DomainIdentificationService` orchestrates Published RKM → packs → AI →
validate → persist (`domain.analyze` audit). Traceability matrix added in Task 8. No HTTP yet.

## 0.3.1-task6 (AI domain identification)

Sprint 3.1 Task 6: `identify_solution_domains` on AIProvider (local/gemini/openai/fallback),
prompt `domain_identification.txt`, and `normalize_domain_identification`. No HTTP service yet.

## 0.3.1-task5 (phase 3 knowledge packs)

Sprint 3.1 Task 5: `phase3_knowledge_packs.py` — catalog-driven domain pack context,
`pack_version()`, detection via aliases + Phase 2 checklist bridge. Stage F packs unchanged.

## 0.3.1-task4 (domain repository)

Sprint 3.1 Task 4: `DomainRepository` with `create_analysis_tree`, version helpers,
and read APIs for domains/links/dependencies/questions/traceability. No HTTP/AI yet.

## 0.3.1-task3 (domain schemas)

Sprint 3.1 Task 3: Pydantic API + AI validation contracts in
`backend/app/schemas/domain.py` (`validate_domain_ai_extraction`, catalog-bound codes,
traceability statuses). No analyze service/API yet.

## 0.3.1-task2 (domain schema)

Sprint 3.1 Task 2: `domain_analyses`, `solution_domains`, links/dependencies/open questions,
and `requirement_traceability` via `07_phase3_domains.sql` + `ensure_schema` + ORM models.
No domain analyze service/API yet.

## 0.3.1-task1 (domain catalog freeze)

Sprint 3.1 Task 1: frozen Phase 3 domain codes in `knowledge/phase3/domains/catalog.json`,
`knowledge/phase3/VERSION`, priority domain overview stubs, and loader
`backend/app/services/phase3_domain_catalog.py`. No domain analyze API yet.

## 0.3.0-sprint3.0 (design lock)

Sprint 3.0 accepted ATLAS-031…034 (and mapped former ADR-017…024 → ATLAS-035…041).
API/DB/MVP fate frozen in `21_PHASE3_DECISIONS.md`. No feature code in this revision.

## 0.3.0 (baseline pack + thin architecture MVP)

Doc pack `01`–`23` added under `docs/Phase 3/`.

**Shipped in code (MVP slice):**
- Architecture recommendation from Published RKM only (ATLAS-023)
- `architecture_models` persistence + generate/get APIs under `/api/v1/projects/{id}/architecture`
- Architecture panel in the project UI
- Vendor-neutral technology categories (no product SKUs)

**Still planned after Sprint 3.1 (see backlog / acceptance):** pattern library, capacity,
scoring, risks/assumptions, vendor catalogue, BOM import/validation, architecture
review/approve, and normalized `/architectures` under the locked `/projects/{id}/…`
surface in `15_API_PHASE3.md`. Domain identification + domain-stage traceability shipped
in `0.3.1` above.

## Revision policy
Do not silently alter the Phase 3 baseline.

Record architectural changes here and in the relevant ADR.
