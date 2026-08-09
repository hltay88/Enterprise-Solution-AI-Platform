# AGENTS.md

Project Atlas — an AI presales assistant (login → create project → upload requirement doc →
AI requirement analysis → clarification questions → Draft/Published RKM → architecture).
Docs index: `docs/README.md`. Phase packs live under `docs/Phase 1/`, `docs/Phase 2/`,
`docs/Phase 3/` (spaces + capital P — do not recreate parallel trees like `docs/Phase3/`).

For **Mac Docker one-command start/stop**, use `./start-atlas.sh` / `./stop-atlas.sh`
(see `docs/Phase 1/LOCAL_START.md`). Cloud agents still prefer the native Postgres + uvicorn +
`npm run dev` flow below.

## Cursor Cloud specific instructions

The environment runs this stack **natively** (not via Docker Compose). The Docker Compose
setup in `docker/` builds the *production* standalone images; for local development we run
Postgres as a system service and the app processes directly with hot reload.

### Services

| Service | Port | Start command | Notes |
|---------|------|---------------|-------|
| PostgreSQL 16 | 5432 | `sudo pg_ctlcluster 16 main start` | System service; **not auto-started** on VM boot — start it before the backend. |
| Backend (FastAPI) | 8000 | `cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | Reads env from `backend/.env` (its CWD). |
| Frontend (Next.js) | 3000 | `cd frontend && npm run dev` | Reads `frontend/.env.local` (`NEXT_PUBLIC_API_URL`). |

Health check: `curl -s http://localhost:8000/api/health` → `status: ok`, `database: ok`.

### Non-obvious caveats

- **Postgres autostart**: the cluster is not started automatically. Run
  `sudo pg_ctlcluster 16 main start` (idempotent-ish: it errors if already online, which is safe
  to ignore) at the start of a session.
- **DB schema bootstrap**: the base tables (`users`, `projects`, ...) and the `pgcrypto`
  extension are created only by `docker/postgres/init/*.sql`. The backend's `ensure_schema()`
  only runs additive `ALTER TABLE ... ADD COLUMN` upgrades — it does **not** create the base
  tables. The `atlas` role/db and schema are already provisioned and persist in the VM. To
  rebuild a fresh DB: create role `atlas` (password `atlas`) + db `atlas`, then run
  `docker/postgres/init/01_extensions.sql` and `02_schema.sql`, and `ALTER ... OWNER TO atlas`
  so the `atlas` role can run `ALTER TABLE` on startup.
- **Native DB URL**: `backend/.env` uses `DATABASE_URL=postgresql://atlas:atlas@localhost:5432/atlas`
  (host `localhost`, not the Compose hostname `db`). `STORAGE_PATH` points at
  `/workspace/storage/uploads`. These local env files (`backend/.env`, `frontend/.env.local`)
  are git-ignored and already exist in the VM.
- **AI runs offline by default**: with no `GEMINI_API_KEY`/`OPENAI_API_KEY`, `ATLAS_AI_PROVIDER=auto`
  falls back to a built-in local heuristic analyzer, so the full flow works without cloud keys.
  Add a key to `backend/.env` to use a real LLM (Gemini free tier recommended); restart the
  backend after changing env.
- **Demo login**: `demo@example.com` / `changeme` (auto-seeded on backend startup; the login
  form is pre-filled with these).

### Lint / test / build

- Frontend lint: `cd frontend && npm run lint` (currently passes with only `react-hooks/exhaustive-deps` warnings).
- There is **no automated test suite** (no pytest, no frontend test script) in this repo.
- Frontend production build (optional): `cd frontend && npm run build`. Dev uses `npm run dev`.
