# Sprint 5.2 — RAG / Knowledge Retrieval (implementation notes)

Status: implemented (Mac-local development target).

## Scope delivered

- pgvector-enabled Postgres image (`pgvector/pgvector:pg16`)
- `knowledge_chunks` with `vector(384)` + FTS (`content_tsv`)
- `retrieval_runs` / `retrieval_results` audit trail
- Provider-neutral embeddings:
  - `ATLAS_EMBEDDING_PROVIDER=auto|local|gemini|openai`
  - local deterministic hash embedder for offline Mac / tests
- Chunk + index on approve/publish (+ `POST /knowledge/{id}/reindex`)
- Hybrid retrieval: vector cosine + Postgres FTS fused via RRF
- Local re-ranker after RRF (lexical overlap + freshness blend)
- Citations (knowledge id/version/chunk/page/section/excerpt)
- Golden-set eval fixtures: `tests/fixtures/rag_golden_set.json`
- APIs: `POST /api/v1/retrieval/search`, `POST /api/v1/retrieval/context`
- UI: `/knowledge/retrieve` Retrieval Explorer

## Eligibility

Only `approved` and `published` knowledge versions are searchable (`RETRIEVAL_ELIGIBLE_STATUSES`).

Insufficient results surface `INSUFFICIENT EVIDENCE — REVIEW REQUIRED`.

## Configuration

| Env | Default | Purpose |
|-----|---------|---------|
| `ATLAS_EMBEDDING_PROVIDER` | `local` | Embeddings backend (`local` recommended on Mac; `auto` falls back at runtime) |
| `ATLAS_EMBEDDING_MODEL` | (provider default) | Model id |
| `ATLAS_EMBEDDING_DIMS` | `384` | Must match DDL `vector(384)` |
| `ATLAS_KNOWLEDGE_CHUNK_SIZE` | `1000` | Chunk chars |
| `ATLAS_KNOWLEDGE_CHUNK_OVERLAP` | `150` | Overlap |
| `ATLAS_RETRIEVAL_TOP_K` | `8` | Default top-k |
| `ATLAS_RETRIEVAL_MIN_SCORE` | `0.05` | RRF score floor |

Changing dims requires a schema/reindex migration (not auto). Prefer one embedding backend per environment.

## Infra note (Mac Docker)

Compose DB image changed from `postgres:16` to `pgvector/pgvector:pg16`.

After pull:

```bash
./stop-atlas.sh
./start-atlas.sh
```

If `CREATE EXTENSION vector` fails on an old volume, recreate DB volume once:

```bash
./stop-atlas.sh --wipe   # destroys local DB data
./start-atlas.sh
```

## Out of scope (later product work)

- Cross-encoder / hosted ML re-rankers (optional upgrade path)
- Shared-tenant project membership / org hierarchy

## Tests

- `tests/test_rag_embeddings_chunking.py`
- `tests/test_phase5_golden_eval.py`
- Existing Phase 1–5 suite must remain green

## Schema

See `docker/postgres/init/13_phase5_rag.sql` and `ensure_schema()` additions.
