-- Phase 3 — Architecture Recommendation Engine

CREATE TABLE IF NOT EXISTS architecture_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    rkm_id UUID REFERENCES requirement_models (id) ON DELETE SET NULL,
    rkm_version_label TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    version_label TEXT NOT NULL DEFAULT '1.0.0',
    version_major INTEGER NOT NULL DEFAULT 1,
    version_minor INTEGER NOT NULL DEFAULT 0,
    version_patch INTEGER NOT NULL DEFAULT 0,
    summary TEXT,
    reasoning_summary TEXT,
    model TEXT,
    prompt_version TEXT,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_architecture_models_project_id
ON architecture_models (project_id);

CREATE INDEX IF NOT EXISTS idx_architecture_models_created_at
ON architecture_models (created_at DESC);
