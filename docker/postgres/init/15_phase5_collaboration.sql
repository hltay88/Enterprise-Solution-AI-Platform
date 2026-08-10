-- Sprint 5.4 — Collaboration, governance, usage

ALTER TABLE audit_logs ALTER COLUMN project_id DROP NOT NULL;

CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    user_id UUID REFERENCES users (id) ON DELETE SET NULL,
    parent_id UUID REFERENCES comments (id) ON DELETE SET NULL,
    body TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_comments_project_created ON comments (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_resource ON comments (resource_type, resource_id);

CREATE TABLE IF NOT EXISTS review_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    requested_by UUID REFERENCES users (id) ON DELETE SET NULL,
    assignee_id UUID REFERENCES users (id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'open',
    message TEXT NOT NULL DEFAULT '',
    resolution_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_review_requests_project ON review_requests (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_review_requests_status ON review_requests (status);

CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    requested_by UUID REFERENCES users (id) ON DELETE SET NULL,
    assignee_id UUID REFERENCES users (id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'open',
    message TEXT NOT NULL DEFAULT '',
    resolution_note TEXT,
    resolved_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_approval_requests_project ON approval_requests (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests (status);

CREATE TABLE IF NOT EXISTS usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    latency_ms INTEGER,
    token_input INTEGER,
    token_output INTEGER,
    estimated_cost_usd DOUBLE PRECISION,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_code TEXT,
    user_id UUID REFERENCES users (id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects (id) ON DELETE SET NULL,
    tenant_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_records_created ON usage_records (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_records_event ON usage_records (event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_records_project ON usage_records (project_id, created_at DESC);
