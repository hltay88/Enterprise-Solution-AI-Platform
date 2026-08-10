# Phase 5 Changelog

## UI + eval gap close (2026-08-10)

Named Phase 5 screens from `19_UI_PHASE5.md`: `/solutions` (Solution Review),
`/approvals` (Approval Center), `/usage` (Usage Dashboard); `/governance`
positioned as Audit Viewer. Golden-set domains expanded for data centre, AV/LED,
digital signage, and smart-building (`21_PHASE5_AI_EVALUATION.md`).

## Phase 5 portable 100% closeout (2026-08-10)

Closed remaining Foundation 0.5 partials with Mac-local / portable depth:

- Local re-ranker after RRF (`rerank.py`) wired into retrieval
- Golden-set RAG + agent eval fixtures and pytest gates
- Specialist local refine path (+ optional `ATLAS_SPECIALIST_LLM`)
- OIDC adapter with `mock://local` auth routes
- Metered billing provider (default) + usage cost estimates
- Security release-gate tests (tenant isolation, rate-limit, write deny, audit no-delete, OIDC mock)

See `27_PHASE5_ACCEPTANCE_AND_HANDOVER.md`.

## Atlas Foundation 0.5 (frozen 2026-08-10)

Enterprise Knowledge Engine, RAG retrieval, multi-agent orchestration (15 specialists),
collaboration/governance, and multi-tenant SaaS foundation — accepted as Mac-local MVP.
Superseded at portable-complete depth by the closeout entry above.

## 0.5.5 — Sprint 5.5
SaaS / multi-tenant foundation MVP.

Added: tenants + memberships; JWT tenant claim; project/knowledge/retrieval/usage
tenant scoping; tenant admin APIs + `/tenants` UI; rate-limit middleware (off by
default); OIDC config stubs; noop billing provider; DB backup script. See
`IMPLEMENTATION_SPRINT_5_5.md`.

## 0.5.4 — Sprint 5.4
Collaboration & governance MVP.

Added: project comments; review/approval requests; activity timeline; permission
catalog on editor/approver; consolidated audit-events + login audit; usage
records/summary with retrieval + agent hooks; Collaboration panel and
`/governance` page. See `IMPLEMENTATION_SPRINT_5_4.md`.

## 0.5.3 — Sprint 5.3
Multi-agent orchestration (advise-only).

Added: agent registry + runs/tool-call audit; **15** runnable specialists covering
the full Phase 5 taxonomy (networking, wireless, security, cloud, data_centre,
compute, storage, backup, hci, av, led_videowall, digital_signage, billboard,
smart_building, iot); read-only tool gateway; orchestrator APIs; Agent Workspace
panel on project detail. See `IMPLEMENTATION_SPRINT_5_3.md`.

## 0.5.0
Enterprise Solution AI Platform baseline.

Added: Enterprise Knowledge Engine, governed knowledge lifecycle, RAG/retrieval, multi-agent orchestration, collaboration/governance, tenant/security foundation, usage/observability and SaaS readiness.
