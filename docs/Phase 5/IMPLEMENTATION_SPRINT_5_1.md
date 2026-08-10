# Sprint 5.1 — Enterprise Knowledge Engine (implementation notes)

Status: implemented (Mac-local development target).

## Scope delivered

- First-class `KnowledgeItem` / `KnowledgeVersion` / `KnowledgeSource` domain
- Extensible taxonomy domains (Phase 5 list seeded in DB)
- Knowledge types vocabulary
- Lifecycle: Draft → Review → Approved → Published → Deprecated → Archived
- Published immutability; edits via `POST /api/v1/knowledge/{id}/new-version`
- Ingestion: PDF, DOCX, PPTX, XLSX, Markdown, TXT (extract + classify + store)
- Nullable `tenant_id` (NULL = platform/default) for future Sprint 5.5
- Knowledge-scoped audit events (`knowledge_audit_events`)
- APIs under `/api/v1/knowledge`
- UI: `/knowledge` library + `/knowledge/[id]` detail
- Config-driven storage via existing `STORAGE_PATH` (no cloud-specific services)

## Explicitly deferred

| Item | Sprint |
|------|--------|
| Chunking / embeddings / vector index | 5.2 |
| Hybrid retrieval / citations | 5.2 |
| Multi-agent orchestration | 5.3 |
| Collaboration comments / review requests | 5.4 |
| Full multi-tenant SaaS / IdP | 5.5 |

## Spec boundary note

`04_KNOWLEDGE_INGESTION.md` describes Chunk → Embed → Index. Per backlog and readiness decision, Sprint 5.1 stops at extract/classify/persist; embedding begins in 5.2. Phase 5 specs were not rewritten.

## Schema

See `docker/postgres/init/12_phase5_knowledge.sql` and additive statements in `backend/app/db/schema.py` (`ensure_schema`).

Key tables: `taxonomy_domains`, `knowledge_items`, `knowledge_versions`, `knowledge_sources`, `knowledge_audit_events`.

## API (summary)

- `GET/POST /api/v1/knowledge` (POST multipart or `POST /json`)
- `GET/PATCH /api/v1/knowledge/{id}`
- `POST .../ingest`, `submit-review`, `approve`, `publish`, `deprecate`, `archive`, `return-draft`, `new-version`
- `GET /api/v1/knowledge/taxonomy/domains|types`

Auth: JWT. Editors create/edit drafts; Approvers approve/publish/deprecate/archive.

## Portability

- Database: `DATABASE_URL`
- Files: `STORAGE_PATH` → `knowledge/{item_id}/...`
- No AWS/Azure/GCP SDK usage in this sprint

## Tests

- `tests/test_knowledge_lifecycle.py`
- `tests/test_knowledge_parsers.py`
- `tests/test_knowledge_service_lifecycle.py`

Run: `cd backend && .venv/bin/pytest`

## Coexistence

Static `knowledge/*.md` prompt packs and Phase 3 catalogs remain unchanged. They are **not** automatically migrated into KnowledgeItems in 5.1.
