-- Project Atlas — PostgreSQL extensions (Sprint 1 + Sprint 5.2)
-- Runs once on first database initialization via docker-entrypoint-initdb.d.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Sprint 5.2 RAG — requires pgvector/pgvector:pg16 (or equivalent) image.
CREATE EXTENSION IF NOT EXISTS vector;
