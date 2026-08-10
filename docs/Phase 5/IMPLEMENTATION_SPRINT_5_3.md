# Sprint 5.3 — Multi-Agent Orchestration (implementation notes)

Status: implemented (Mac-local development target).

## Scope delivered

- Agent registry (`agents`) with **15 runnable specialists** covering the full
  Phase 5 knowledge taxonomy:
  networking, wireless, security, cloud, data_centre, compute, storage, backup,
  hci, av, led_videowall, digital_signage, billboard, smart_building, iot
- Advise-only orchestrator runs (`agent_runs`) with tool-call audit (`agent_tool_calls`)
- Read-only tool gateway:
  - `knowledge_search`, `get_project`, `get_published_rkm`
  - `get_domain_analysis`, `get_architectures`, `search_vendor_catalogue`
  - write tools explicitly denied (`approve_rkm`, `generate_architecture`, etc.)
- Specialists: all registered domain agents above (local heuristic, RAG-grounded)
- Conflict surfacing across security/cloud, wireless/security, storage/backup, and related pairs
- APIs:
  - `GET /api/v1/agents`
  - `POST /api/v1/projects/{id}/agent-runs`
  - `GET /api/v1/projects/{id}/agent-runs`
  - `GET /api/v1/agent-runs/{run_id}`
- UI: Agent Workspace panel on project detail (`AgentWorkspacePanel`)

## Guarantees

- Agents **cannot** approve or mutate RKM / architecture / BOM (ADR-038)
- Knowledge retrieval still limited to approved/published versions (Sprint 5.2)
- Runs are advisory; `review_required` surfaces insufficient evidence / conflicts

## Local / Mac notes

Specialists use local heuristics + RAG search (no cloud LLM required). With
`ATLAS_EMBEDDING_PROVIDER=local`, agent knowledge grounding works offline.

## Schema

See `docker/postgres/init/14_phase5_agents.sql` and `ensure_schema()` Sprint 5.3 block.

## Tests

- `backend/tests/test_agents_sprint53.py`
- Existing Phase 1–5.2 suite must remain green

## Out of scope (later)

- Deeper domain-specific heuristic packs / LLM-authored specialist prose as primary path
- Collaboration / multi-tenancy (5.4 / 5.5)
- Auto-apply agent recommendations into design artifacts
