-- Sprint 5.1 — Enterprise Knowledge Engine
-- Additive schema; tenant_id is nullable until Sprint 5.5 multi-tenancy.

CREATE TABLE IF NOT EXISTS taxonomy_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    project_id UUID REFERENCES projects (id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    knowledge_type TEXT NOT NULL DEFAULT 'best_practice',
    domain_code TEXT NOT NULL DEFAULT 'networking',
    owner_user_id UUID REFERENCES users (id) ON DELETE SET NULL,
    sensitivity TEXT NOT NULL DEFAULT 'internal',
    current_version_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_items_tenant_id ON knowledge_items (tenant_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_project_id ON knowledge_items (project_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_domain_code ON knowledge_items (domain_code);

CREATE TABLE IF NOT EXISTS knowledge_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_item_id UUID NOT NULL REFERENCES knowledge_items (id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL DEFAULT 1,
    version_label TEXT NOT NULL DEFAULT '1',
    status TEXT NOT NULL DEFAULT 'draft',
    content_text TEXT,
    content_location TEXT,
    change_summary TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    tags TEXT[] NOT NULL DEFAULT '{}',
    effective_date DATE,
    expiry_date DATE,
    next_review_date DATE,
    source_document_name TEXT,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    reviewed_by UUID REFERENCES users (id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users (id) ON DELETE SET NULL,
    published_by UUID REFERENCES users (id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_knowledge_versions_item_version UNIQUE (knowledge_item_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_versions_item_id ON knowledge_versions (knowledge_item_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_versions_status ON knowledge_versions (status);

CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_version_id UUID NOT NULL REFERENCES knowledge_versions (id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT,
    storage_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    checksum_sha256 TEXT NOT NULL,
    page_count INTEGER,
    extract_warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    section_hints JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_sources_version_id
ON knowledge_sources (knowledge_version_id);

CREATE TABLE IF NOT EXISTS knowledge_audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    knowledge_item_id UUID REFERENCES knowledge_items (id) ON DELETE SET NULL,
    knowledge_version_id UUID,
    user_id UUID REFERENCES users (id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_audit_events_item_id
ON knowledge_audit_events (knowledge_item_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_audit_events_tenant_id
ON knowledge_audit_events (tenant_id);

-- Seed Phase 5 taxonomy domains (idempotent).
INSERT INTO taxonomy_domains (code, name, aliases)
VALUES
    ('networking', 'Networking', ARRAY['campus_lan', 'wan_sdwan', 'internet', 'network']),
    ('wireless', 'Wireless', ARRAY['wifi', 'wlan', 'wi-fi']),
    ('cybersecurity', 'Cybersecurity', ARRAY['security', 'network_security', 'identity']),
    ('cloud', 'Cloud', ARRAY[]::TEXT[]),
    ('data_centre', 'Data Centre', ARRAY['data_center', 'dc', 'datacentre']),
    ('compute', 'Compute', ARRAY['virtualization']),
    ('storage', 'Storage', ARRAY[]::TEXT[]),
    ('backup', 'Backup', ARRAY['backup_dr', 'dr']),
    ('hci', 'HCI', ARRAY['hyperconverged']),
    ('av', 'AV', ARRAY['audio_visual', 'collaboration', 'meeting_rooms']),
    ('led_videowall', 'LED Videowall', ARRAY['led', 'led_video_wall', 'av_led']),
    ('digital_signage', 'Digital Signage', ARRAY[]::TEXT[]),
    ('billboard', 'Billboard', ARRAY[]::TEXT[]),
    ('smart_building', 'Smart Building', ARRAY['iot_smart_building']),
    ('iot', 'IoT', ARRAY['cctv', 'monitoring_observability'])
ON CONFLICT (code) DO NOTHING;
