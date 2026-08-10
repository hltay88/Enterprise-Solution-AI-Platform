# Copy to .env for local Docker Compose (do not commit .env)

# Database
# Inside Docker Compose use host `db`. On the host machine use `localhost`.
DATABASE_URL=postgresql://atlas:atlas@db:5432/atlas
POSTGRES_USER=atlas
POSTGRES_PASSWORD=atlas
POSTGRES_DB=atlas

# Auth (ATLAS-011)
SECRET_KEY=change-me-in-local-dev
JWT_EXPIRE_MINUTES=60
DEMO_USER_EMAIL=demo@example.com
DEMO_USER_PASSWORD=changeme
DEMO_USER_NAME=Atlas Demo

# AI — provider-independent (ATLAS-012)
# Recommended for local demo: Gemini free tier from Google AI Studio
#   https://aistudio.google.com/apikey
# Paste keys with no quotes/spaces. Keep this file at the repo root as `.env`.
# After changing values, recreate backend (restart alone will not reload env):
#   docker compose -f docker/docker-compose.yml --env-file .env up -d --build --force-recreate backend
# Required for Gemini cloud analysis. Paste key with no quotes/spaces.
GEMINI_API_KEY=
# Prefer gemini-flash-latest for new free-tier keys (gemini-2.0-flash often returns 429)
GEMINI_MODEL=gemini-flash-latest

# Optional paid/alternative provider
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# auto = Gemini (if keyed) -> OpenAI (if keyed) -> local fallback
# gemini | openai | local
ATLAS_AI_PROVIDER=auto

# Sprint 5.2 RAG embeddings (provider-neutral)
# local = deterministic hash (recommended for Mac offline / reliable default)
# auto = Gemini (if keyed) -> OpenAI (if keyed) -> local, with runtime fallback
ATLAS_EMBEDDING_PROVIDER=local
ATLAS_EMBEDDING_MODEL=
ATLAS_EMBEDDING_DIMS=384
ATLAS_KNOWLEDGE_CHUNK_SIZE=1000
ATLAS_KNOWLEDGE_CHUNK_OVERLAP=150
ATLAS_RETRIEVAL_TOP_K=8
ATLAS_RETRIEVAL_MIN_SCORE=0.05

# Optional future providers
ANTHROPIC_API_KEY=

# File storage (ATLAS-013 / ATLAS-027 Phase 2.1)
STORAGE_PATH=/app/storage/uploads
MAX_UPLOAD_MB=50
MAX_BATCH_UPLOAD_MB=200

# Domain clarification checklists (mounted from repo knowledge/ in Compose)
KNOWLEDGE_PATH=/app/knowledge

# Backend
CORS_ORIGINS=http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
