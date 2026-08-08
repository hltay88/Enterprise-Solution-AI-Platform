-- Phase 2 Stage C — Draft Requirement Knowledge Model (ATLAS-020 / ATLAS-021 / ATLAS-024)

CREATE TABLE IF NOT EXISTS requirement_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'ai_generated',
    version_major INTEGER NOT NULL DEFAULT 1,
    version_minor INTEGER NOT NULL DEFAULT 0,
    version_patch INTEGER NOT NULL DEFAULT 0,
    version_label TEXT NOT NULL DEFAULT '1.0.0',
    is_active_draft BOOLEAN NOT NULL DEFAULT TRUE,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    completeness_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    consistency_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    evidence_coverage DOUBLE PRECISION NOT NULL DEFAULT 0,
    reasoning_summary TEXT,
    prompt_version TEXT,
    model TEXT,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_requirement_models_project_id
    ON requirement_models (project_id);
CREATE INDEX IF NOT EXISTS idx_requirement_models_active_draft
    ON requirement_models (project_id)
    WHERE is_active_draft = TRUE;

CREATE TABLE IF NOT EXISTS requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rkm_id UUID NOT NULL REFERENCES requirement_models (id) ON DELETE CASCADE,
    section TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'draft',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_requirements_rkm_id ON requirements (rkm_id);
CREATE INDEX IF NOT EXISTS idx_requirements_section ON requirements (rkm_id, section);

CREATE TABLE IF NOT EXISTS requirement_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rkm_id UUID NOT NULL REFERENCES requirement_models (id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    document_id UUID REFERENCES requirement_documents (id) ON DELETE SET NULL,
    page INTEGER,
    excerpt TEXT,
    field_name TEXT,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_requirement_evidence_rkm_id
    ON requirement_evidence (rkm_id);
CREATE INDEX IF NOT EXISTS idx_requirement_evidence_source_type
    ON requirement_evidence (rkm_id, source_type);

CREATE TABLE IF NOT EXISTS requirement_evidence_links (
    requirement_id UUID NOT NULL REFERENCES requirements (id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES requirement_evidence (id) ON DELETE CASCADE,
    PRIMARY KEY (requirement_id, evidence_id)
);
