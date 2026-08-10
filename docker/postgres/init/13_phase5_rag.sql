-- Sprint 5.2 — Knowledge chunks, embeddings (pgvector), retrieval audit.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_item_id UUID NOT NULL REFERENCES knowledge_items (id) ON DELETE CASCADE,
    knowledge_version_id UUID NOT NULL REFERENCES knowledge_versions (id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    page_number INTEGER,
    section_label TEXT,
    embedding vector(384),
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED,
    embedding_provider TEXT,
    embedding_model TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_knowledge_chunks_version_index UNIQUE (knowledge_version_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_item_id ON knowledge_chunks (knowledge_item_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_version_id ON knowledge_chunks (knowledge_version_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_tsv ON knowledge_chunks USING GIN (content_tsv);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding
ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS retrieval_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    user_id UUID REFERENCES users (id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    top_k INTEGER NOT NULL DEFAULT 8,
    embedding_provider TEXT,
    embedding_model TEXT,
    latency_ms INTEGER,
    result_count INTEGER NOT NULL DEFAULT 0,
    insufficient_evidence BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_retrieval_runs_user_id ON retrieval_runs (user_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_runs_created_at ON retrieval_runs (created_at DESC);

CREATE TABLE IF NOT EXISTS retrieval_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    retrieval_run_id UUID NOT NULL REFERENCES retrieval_runs (id) ON DELETE CASCADE,
    knowledge_chunk_id UUID REFERENCES knowledge_chunks (id) ON DELETE SET NULL,
    knowledge_item_id UUID,
    knowledge_version_id UUID,
    rank INTEGER NOT NULL,
    vector_score DOUBLE PRECISION,
    keyword_score DOUBLE PRECISION,
    fused_score DOUBLE PRECISION,
    citation JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_retrieval_results_run_id ON retrieval_results (retrieval_run_id);
