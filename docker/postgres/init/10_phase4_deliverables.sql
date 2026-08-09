-- Phase 4 Sprint 4.1 — Deliverables foundation (ATLAS-042…048)
-- Proposal generator: snapshots, templates, generated documents, export jobs.
-- Does not touch Phase 2 requirement_documents /documents ingest.

CREATE TABLE IF NOT EXISTS document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_templates_type_code UNIQUE (document_type, code)
);

CREATE INDEX IF NOT EXISTS idx_document_templates_document_type
ON document_templates (document_type);

CREATE TABLE IF NOT EXISTS template_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES document_templates (id) ON DELETE CASCADE,
    version_label TEXT NOT NULL DEFAULT '1.0.0',
    version_major INTEGER NOT NULL DEFAULT 1,
    version_minor INTEGER NOT NULL DEFAULT 0,
    version_patch INTEGER NOT NULL DEFAULT 0,
    sections_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    styles_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    rendering_rules_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_template_versions_template_semver
        UNIQUE (template_id, version_major, version_minor, version_patch)
);

CREATE INDEX IF NOT EXISTS idx_template_versions_template_id
ON template_versions (template_id);

CREATE TABLE IF NOT EXISTS source_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    rkm_id UUID REFERENCES requirement_models (id) ON DELETE SET NULL,
    rkm_version_label TEXT,
    architecture_id UUID REFERENCES architecture_options (id) ON DELETE SET NULL,
    architecture_version_label TEXT,
    bom_import_id UUID REFERENCES bom_imports (id) ON DELETE SET NULL,
    catalogue_id UUID REFERENCES vendor_catalogues (id) ON DELETE SET NULL,
    catalogue_version_label TEXT,
    knowledge_pack_version TEXT,
    prompt_version TEXT,
    model TEXT,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    bom_validated BOOLEAN NOT NULL DEFAULT FALSE,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_source_snapshots_project_id
ON source_snapshots (project_id);

CREATE INDEX IF NOT EXISTS idx_source_snapshots_architecture_id
ON source_snapshots (architecture_id);

CREATE TABLE IF NOT EXISTS generation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    document_type TEXT NOT NULL DEFAULT 'proposal',
    source_snapshot_id UUID NOT NULL REFERENCES source_snapshots (id) ON DELETE CASCADE,
    template_version_id UUID REFERENCES template_versions (id) ON DELETE SET NULL,
    model TEXT,
    prompt_version TEXT,
    status TEXT NOT NULL DEFAULT 'completed',
    raw_payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generation_runs_project_id
ON generation_runs (project_id);

CREATE INDEX IF NOT EXISTS idx_generation_runs_snapshot_id
ON generation_runs (source_snapshot_id);

CREATE TABLE IF NOT EXISTS generated_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    document_type TEXT NOT NULL DEFAULT 'proposal',
    title TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    template_id UUID REFERENCES document_templates (id) ON DELETE SET NULL,
    template_version_id UUID REFERENCES template_versions (id) ON DELETE SET NULL,
    source_snapshot_id UUID NOT NULL REFERENCES source_snapshots (id) ON DELETE RESTRICT,
    generation_run_id UUID REFERENCES generation_runs (id) ON DELETE SET NULL,
    current_version_id UUID,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users (id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generated_documents_project_id
ON generated_documents (project_id);

CREATE INDEX IF NOT EXISTS idx_generated_documents_project_type
ON generated_documents (project_id, document_type);

CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES generated_documents (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    version_label TEXT NOT NULL DEFAULT '1.0.0',
    version_major INTEGER NOT NULL DEFAULT 1,
    version_minor INTEGER NOT NULL DEFAULT 0,
    version_patch INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    source_snapshot_id UUID NOT NULL REFERENCES source_snapshots (id) ON DELETE RESTRICT,
    template_version_id UUID REFERENCES template_versions (id) ON DELETE SET NULL,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users (id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_versions_semver
        UNIQUE (document_id, version_major, version_minor, version_patch)
);

CREATE INDEX IF NOT EXISTS idx_document_versions_document_id
ON document_versions (document_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_generated_documents_current_version_id'
    ) THEN
        ALTER TABLE generated_documents
            ADD CONSTRAINT fk_generated_documents_current_version_id
            FOREIGN KEY (current_version_id)
            REFERENCES document_versions (id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS document_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES document_versions (id) ON DELETE CASCADE,
    section_type TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    sequence INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
    assumptions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_sections_version_id
ON document_sections (document_version_id);

CREATE TABLE IF NOT EXISTS content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID NOT NULL REFERENCES document_sections (id) ON DELETE CASCADE,
    content_type TEXT NOT NULL DEFAULT 'paragraph',
    text TEXT NOT NULL DEFAULT '',
    structured_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
    approval_status TEXT NOT NULL DEFAULT 'draft',
    sort_order INTEGER NOT NULL DEFAULT 0,
    review_required BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_content_items_section_id
ON content_items (section_id);

CREATE TABLE IF NOT EXISTS document_source_refs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_item_id UUID NOT NULL REFERENCES content_items (id) ON DELETE CASCADE,
    ref_kind TEXT NOT NULL,
    ref_id TEXT,
    label TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_source_refs_content_item_id
ON document_source_refs (content_item_id);

CREATE TABLE IF NOT EXISTS document_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES document_versions (id) ON DELETE CASCADE,
    approver_id UUID REFERENCES users (id) ON DELETE SET NULL,
    decision TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_approvals_version_id
ON document_approvals (document_version_id);

CREATE TABLE IF NOT EXISTS export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES generated_documents (id) ON DELETE CASCADE,
    document_version_id UUID NOT NULL REFERENCES document_versions (id) ON DELETE CASCADE,
    format TEXT NOT NULL DEFAULT 'docx',
    status TEXT NOT NULL DEFAULT 'queued',
    storage_path TEXT,
    checksum_sha256 TEXT,
    page_count INTEGER,
    error TEXT,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_export_jobs_project_id
ON export_jobs (project_id);

CREATE INDEX IF NOT EXISTS idx_export_jobs_document_id
ON export_jobs (document_id);

-- Seed default proposal template (idempotent)
INSERT INTO document_templates (id, document_type, code, name, active)
SELECT gen_random_uuid(), 'proposal', 'default_proposal', 'Default Proposal', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM document_templates
    WHERE document_type = 'proposal' AND code = 'default_proposal'
);

INSERT INTO template_versions (
    template_id, version_label, version_major, version_minor, version_patch,
    sections_json, styles_json, rendering_rules_json, status
)
SELECT
    t.id,
    '1.0.0', 1, 0, 0,
    '[
      {"section_type":"cover","title":"Cover"},
      {"section_type":"executive_summary","title":"Executive Summary"},
      {"section_type":"customer_understanding","title":"Customer Understanding"},
      {"section_type":"challenges","title":"Challenges"},
      {"section_type":"requirements","title":"Requirements"},
      {"section_type":"proposed_solution","title":"Proposed Solution"},
      {"section_type":"architecture","title":"Architecture"},
      {"section_type":"solution_components","title":"Solution Components"},
      {"section_type":"benefits","title":"Benefits"},
      {"section_type":"implementation_approach","title":"Implementation Approach"},
      {"section_type":"timeline","title":"Timeline"},
      {"section_type":"assumptions","title":"Assumptions"},
      {"section_type":"risks","title":"Risks"},
      {"section_type":"exclusions","title":"Exclusions"},
      {"section_type":"support_warranty","title":"Support / Warranty"},
      {"section_type":"next_steps","title":"Next Steps"}
    ]'::jsonb,
    '{"format":"docx"}'::jsonb,
    '{"include_draft_watermark": true}'::jsonb,
    'active'
FROM document_templates t
WHERE t.document_type = 'proposal' AND t.code = 'default_proposal'
  AND NOT EXISTS (
      SELECT 1 FROM template_versions tv
      WHERE tv.template_id = t.id
        AND tv.version_major = 1 AND tv.version_minor = 0 AND tv.version_patch = 0
  );

-- Sprint 4.2 — presentation template seed (idempotent)
INSERT INTO document_templates (id, document_type, code, name, active)
SELECT gen_random_uuid(), 'presentation', 'default_presentation', 'Default Presentation', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM document_templates
    WHERE document_type = 'presentation' AND code = 'default_presentation'
);

INSERT INTO template_versions (
    template_id, version_label, version_major, version_minor, version_patch,
    sections_json, styles_json, rendering_rules_json, status
)
SELECT
    t.id,
    '1.0.0', 1, 0, 0,
    '[
      {"section_type":"title","title":"Title"},
      {"section_type":"executive_summary","title":"Executive Summary"},
      {"section_type":"customer_situation","title":"Customer Situation"},
      {"section_type":"challenges","title":"Challenges"},
      {"section_type":"requirements","title":"Requirements"},
      {"section_type":"proposed_architecture","title":"Proposed Architecture"},
      {"section_type":"solution_overview","title":"Solution Overview"},
      {"section_type":"key_components","title":"Key Components"},
      {"section_type":"technical_highlights","title":"Technical Highlights"},
      {"section_type":"benefits","title":"Benefits"},
      {"section_type":"implementation","title":"Implementation"},
      {"section_type":"timeline","title":"Timeline"},
      {"section_type":"risks_assumptions","title":"Risks / Assumptions"},
      {"section_type":"next_steps","title":"Next Steps"}
    ]'::jsonb,
    '{"format":"pptx"}'::jsonb,
    '{"include_draft_watermark": true}'::jsonb,
    'active'
FROM document_templates t
WHERE t.document_type = 'presentation' AND t.code = 'default_presentation'
  AND NOT EXISTS (
      SELECT 1 FROM template_versions tv
      WHERE tv.template_id = t.id
        AND tv.version_major = 1 AND tv.version_minor = 0 AND tv.version_patch = 0
  );
