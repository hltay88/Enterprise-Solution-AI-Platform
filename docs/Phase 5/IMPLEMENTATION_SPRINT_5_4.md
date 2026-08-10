# Sprint 5.4 — Collaboration & Governance (implementation notes)

Status: **implemented** (Mac-local development target).

## Scope delivered

- Collaboration tables: `comments`, `review_requests`, `approval_requests`
- Usage observability: `usage_records` (+ listing/summary APIs)
- Permission catalog mapped from existing `editor` / `approver` roles
- Project APIs: comments, review/approval requests, activity timeline
- Approver APIs: `GET /audit-events`, `GET /usage`, `GET /usage/summary`
- Login audit (`auth.login` / `auth.login.failed`) with nullable `audit_logs.project_id`
- Usage hooks on retrieval search and agent orchestrator runs
- UI: Collaboration panel on project page; `/governance` usage + audit view
- Schema: `docker/postgres/init/15_phase5_collaboration.sql` + `ensure_schema()`

## Guarantees

- Agents remain advise-only (cannot comment/approve via tools)
- Ordinary users cannot delete audit rows (no delete API)
- Artifact approve/publish paths unchanged; approval requests are an overlay

## Tests

- `backend/tests/test_collaboration_sprint54.py`
- Existing Phase 1–5.3 suite must remain green

## Out of scope (Sprint 5.5+)

- True multi-tenant RBAC / tenant administration
- Enterprise IdP / SSO
- Billing, alerts, hash-chained WORM audit
- Mentions / email / Slack notifications
