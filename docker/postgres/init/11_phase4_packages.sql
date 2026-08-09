-- Phase 4 Sprint 4.4 — BOM template + document packages (ATLAS-050)

INSERT INTO document_templates (id, document_type, code, name, active)
SELECT gen_random_uuid(), 'bom', 'default_bom', 'Default BOM Package Sheet', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM document_templates
    WHERE document_type = 'bom' AND code = 'default_bom'
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
      {"section_type":"line_items","title":"Line Items"},
      {"section_type":"classification","title":"Classification"},
      {"section_type":"issues","title":"Issues"},
      {"section_type":"sources","title":"Sources"}
    ]'::jsonb,
    '{"format":"xlsx"}'::jsonb,
    '{"include_draft_watermark": true}'::jsonb,
    'active'
FROM document_templates t
WHERE t.document_type = 'bom' AND t.code = 'default_bom'
  AND NOT EXISTS (
      SELECT 1 FROM template_versions tv
      WHERE tv.template_id = t.id
        AND tv.version_major = 1 AND tv.version_minor = 0 AND tv.version_patch = 0
  );

CREATE TABLE IF NOT EXISTS document_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Document Package',
    status TEXT NOT NULL DEFAULT 'draft',
    version_label TEXT NOT NULL DEFAULT '1.0.0',
    source_snapshot_id UUID NOT NULL REFERENCES source_snapshots (id) ON DELETE RESTRICT,
    bom_import_id UUID REFERENCES bom_imports (id) ON DELETE SET NULL,
    architecture_id UUID REFERENCES architecture_options (id) ON DELETE SET NULL,
    validation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    findings_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    export_storage_path TEXT,
    export_checksum_sha256 TEXT,
    exported_at TIMESTAMPTZ,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users (id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_packages_project_id
ON document_packages (project_id);

CREATE TABLE IF NOT EXISTS document_package_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id UUID NOT NULL REFERENCES document_packages (id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES generated_documents (id) ON DELETE CASCADE,
    document_version_id UUID NOT NULL REFERENCES document_versions (id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'required',
    checksum_sha256 TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_package_members_package_type UNIQUE (package_id, document_type)
);

CREATE INDEX IF NOT EXISTS idx_document_package_members_package_id
ON document_package_members (package_id);
