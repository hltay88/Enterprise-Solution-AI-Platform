-- Project Atlas — Sprint 1 / 1.1 schema (docs/Phase 1/DATABASE.md)
-- Runs once on first database initialization via docker-entrypoint-initdb.d.

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    project_name TEXT NOT NULL,
    customer TEXT,
    industry TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    account_manager TEXT,
    deal_id TEXT,
    deal_name TEXT,
    pic_name TEXT,
    pic_contact TEXT,
    pic_designation TEXT,
    budget_information TEXT,
    request_type TEXT,
    required_completion_date DATE,
    requirement_details TEXT,
    winning_probability INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects (user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects (status);
CREATE INDEX IF NOT EXISTS idx_projects_request_type ON projects (request_type);

CREATE TABLE IF NOT EXISTS requirement_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    extracted_text TEXT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_requirement_documents_project_id
    ON requirement_documents (project_id);

CREATE TABLE IF NOT EXISTS requirement_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    business_objectives TEXT,
    functional_requirements TEXT,
    non_functional_requirements TEXT,
    assumptions TEXT,
    risks TEXT,
    analysis_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_requirement_analysis_project_id
    ON requirement_analysis (project_id);

CREATE TABLE IF NOT EXISTS clarification_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clarification_questions_project_id
    ON clarification_questions (project_id);
CREATE INDEX IF NOT EXISTS idx_clarification_questions_status
    ON clarification_questions (status);
