-- Phase 3 Sprint 3.1 — Solution Domain Identification (ATLAS-032)
-- Normalized domain analysis + requirement→domain traceability.
-- Reuses projects / requirement_models. Does not create solution_projects.

CREATE TABLE IF NOT EXISTS domain_analyses (
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
    model TEXT,
    prompt_version TEXT,
    knowledge_pack_version TEXT,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_domain_analyses_project_id
ON domain_analyses (project_id);

CREATE INDEX IF NOT EXISTS idx_domain_analyses_created_at
ON domain_analyses (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_domain_analyses_rkm_id
ON domain_analyses (rkm_id);

CREATE TABLE IF NOT EXISTS solution_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES domain_analyses (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    domain_code TEXT NOT NULL,
    name TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
    mandatory_or_optional TEXT NOT NULL DEFAULT 'mandatory',
    selection_source TEXT NOT NULL DEFAULT 'requirement',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_solution_domains_analysis_code UNIQUE (analysis_id, domain_code)
);

CREATE INDEX IF NOT EXISTS idx_solution_domains_analysis_id
ON solution_domains (analysis_id);

CREATE INDEX IF NOT EXISTS idx_solution_domains_project_id
ON solution_domains (project_id);

CREATE INDEX IF NOT EXISTS idx_solution_domains_domain_code
ON solution_domains (domain_code);

-- requirement_id is the RKM requirement identifier (TEXT), not a hard FK to
-- requirements.id, so payload-native IDs remain stable across RKM versions.
CREATE TABLE IF NOT EXISTS domain_requirement_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES solution_domains (id) ON DELETE CASCADE,
    requirement_id TEXT NOT NULL,
    evidence TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_domain_requirement_links UNIQUE (domain_id, requirement_id)
);

CREATE INDEX IF NOT EXISTS idx_domain_requirement_links_domain_id
ON domain_requirement_links (domain_id);

CREATE INDEX IF NOT EXISTS idx_domain_requirement_links_requirement_id
ON domain_requirement_links (requirement_id);

CREATE TABLE IF NOT EXISTS domain_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES solution_domains (id) ON DELETE CASCADE,
    depends_on_domain_code TEXT NOT NULL,
    dependency_kind TEXT NOT NULL DEFAULT 'required',
    reason TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_domain_dependencies_domain_id
ON domain_dependencies (domain_id);

CREATE INDEX IF NOT EXISTS idx_domain_dependencies_depends_on
ON domain_dependencies (depends_on_domain_code);

CREATE TABLE IF NOT EXISTS domain_open_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES domain_analyses (id) ON DELETE CASCADE,
    domain_id UUID REFERENCES solution_domains (id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    affects_selection BOOLEAN NOT NULL DEFAULT TRUE,
    related_requirement_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_domain_open_questions_analysis_id
ON domain_open_questions (analysis_id);

CREATE INDEX IF NOT EXISTS idx_domain_open_questions_domain_id
ON domain_open_questions (domain_id);

-- Sprint 3.1 slice: requirement → domain. Later stages fill architecture/component/decision.
CREATE TABLE IF NOT EXISTS requirement_traceability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    analysis_id UUID NOT NULL REFERENCES domain_analyses (id) ON DELETE CASCADE,
    requirement_id TEXT NOT NULL,
    domain_id UUID REFERENCES solution_domains (id) ON DELETE SET NULL,
    architecture_id UUID,
    component_id UUID,
    decision_id UUID,
    evidence TEXT,
    status TEXT NOT NULL DEFAULT 'not_covered',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_requirement_traceability_project_id
ON requirement_traceability (project_id);

CREATE INDEX IF NOT EXISTS idx_requirement_traceability_analysis_id
ON requirement_traceability (analysis_id);

CREATE INDEX IF NOT EXISTS idx_requirement_traceability_requirement_id
ON requirement_traceability (requirement_id);

CREATE INDEX IF NOT EXISTS idx_requirement_traceability_domain_id
ON requirement_traceability (domain_id);

CREATE INDEX IF NOT EXISTS idx_requirement_traceability_status
ON requirement_traceability (status);
