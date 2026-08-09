-- Phase 3 Sprint 3.2 — Normalized architecture candidates (ATLAS-032 / ATLAS-034)
-- Replaces long-term use of architecture_models.payload_json as system of record.
-- Reuses projects / requirement_models / domain_analyses. No solution_projects.

CREATE TABLE IF NOT EXISTS architecture_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    rkm_id UUID REFERENCES requirement_models (id) ON DELETE SET NULL,
    rkm_version_label TEXT,
    domain_analysis_id UUID REFERENCES domain_analyses (id) ON DELETE SET NULL,
    generation_id UUID NOT NULL,
    candidate_key TEXT NOT NULL DEFAULT 'standard',
    title TEXT NOT NULL DEFAULT '',
    summary TEXT,
    reasoning_summary TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
    overall_score DOUBLE PRECISION,
    pattern_codes JSONB NOT NULL DEFAULT '[]'::jsonb,
    version_label TEXT NOT NULL DEFAULT '1.0.0',
    version_major INTEGER NOT NULL DEFAULT 1,
    version_minor INTEGER NOT NULL DEFAULT 0,
    version_patch INTEGER NOT NULL DEFAULT 0,
    model TEXT,
    prompt_version TEXT,
    knowledge_pack_version TEXT,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_architecture_options_version_candidate
        UNIQUE (project_id, version_major, version_minor, version_patch, candidate_key)
);

CREATE INDEX IF NOT EXISTS idx_architecture_options_project_id
ON architecture_options (project_id);

CREATE INDEX IF NOT EXISTS idx_architecture_options_generation_id
ON architecture_options (generation_id);

CREATE INDEX IF NOT EXISTS idx_architecture_options_domain_analysis_id
ON architecture_options (domain_analysis_id);

CREATE INDEX IF NOT EXISTS idx_architecture_options_created_at
ON architecture_options (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_architecture_options_status
ON architecture_options (status);

CREATE TABLE IF NOT EXISTS architecture_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    purpose TEXT NOT NULL DEFAULT '',
    component_kind TEXT NOT NULL DEFAULT 'logical',
    sort_order INTEGER NOT NULL DEFAULT 0,
    maps_to_requirements JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_architecture_components_architecture_id
ON architecture_components (architecture_id);

CREATE TABLE IF NOT EXISTS architecture_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
    from_component_id UUID NOT NULL REFERENCES architecture_components (id) ON DELETE CASCADE,
    to_component_id UUID NOT NULL REFERENCES architecture_components (id) ON DELETE CASCADE,
    relationship_kind TEXT NOT NULL DEFAULT 'connects_to',
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_architecture_relationships_architecture_id
ON architecture_relationships (architecture_id);

CREATE TABLE IF NOT EXISTS design_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL DEFAULT '',
    impact TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_design_decisions_architecture_id
ON design_decisions (architecture_id);

CREATE TABLE IF NOT EXISTS architecture_assumptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    statement TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    affected_component_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    validation_required BOOLEAN NOT NULL DEFAULT TRUE,
    status TEXT NOT NULL DEFAULT 'unvalidated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_architecture_assumptions_architecture_id
ON architecture_assumptions (architecture_id);

CREATE INDEX IF NOT EXISTS idx_architecture_assumptions_project_id
ON architecture_assumptions (project_id);

CREATE TABLE IF NOT EXISTS solution_risks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'technical',
    cause TEXT NOT NULL DEFAULT '',
    impact TEXT NOT NULL DEFAULT '',
    probability TEXT NOT NULL DEFAULT 'medium',
    severity TEXT NOT NULL DEFAULT 'medium',
    mitigation TEXT NOT NULL DEFAULT '',
    owner TEXT,
    related_requirement_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_solution_risks_architecture_id
ON solution_risks (architecture_id);

CREATE INDEX IF NOT EXISTS idx_solution_risks_project_id
ON solution_risks (project_id);

CREATE TABLE IF NOT EXISTS solution_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
    dimension TEXT NOT NULL,
    weight DOUBLE PRECISION NOT NULL DEFAULT 0,
    score DOUBLE PRECISION NOT NULL DEFAULT 0,
    explanation TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_solution_scores_architecture_dimension
        UNIQUE (architecture_id, dimension)
);

CREATE INDEX IF NOT EXISTS idx_solution_scores_architecture_id
ON solution_scores (architecture_id);

CREATE TABLE IF NOT EXISTS capacity_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    input_value TEXT,
    unit TEXT,
    method TEXT,
    assumption TEXT,
    result TEXT,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
    related_requirement_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    open_question TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_capacity_notes_architecture_id
ON capacity_notes (architecture_id);

CREATE INDEX IF NOT EXISTS idx_capacity_notes_project_id
ON capacity_notes (project_id);

-- Additive FKs for Sprint 3.1 requirement_traceability reserved columns.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_requirement_traceability_architecture_id'
    ) THEN
        ALTER TABLE requirement_traceability
            ADD CONSTRAINT fk_requirement_traceability_architecture_id
            FOREIGN KEY (architecture_id)
            REFERENCES architecture_options (id)
            ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_requirement_traceability_component_id'
    ) THEN
        ALTER TABLE requirement_traceability
            ADD CONSTRAINT fk_requirement_traceability_component_id
            FOREIGN KEY (component_id)
            REFERENCES architecture_components (id)
            ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_requirement_traceability_decision_id'
    ) THEN
        ALTER TABLE requirement_traceability
            ADD CONSTRAINT fk_requirement_traceability_decision_id
            FOREIGN KEY (decision_id)
            REFERENCES design_decisions (id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_requirement_traceability_architecture_id
ON requirement_traceability (architecture_id);

CREATE INDEX IF NOT EXISTS idx_requirement_traceability_component_id
ON requirement_traceability (component_id);

CREATE INDEX IF NOT EXISTS idx_requirement_traceability_decision_id
ON requirement_traceability (decision_id);
