"""Lightweight schema upgrades for local Sprint 1 / Phase 2 development."""

from sqlalchemy import text

from app.db.session import engine


def ensure_schema() -> None:
    """Apply additive schema changes that init SQL may not have run yet."""
    statements = [
        """
        ALTER TABLE requirement_documents
        ADD COLUMN IF NOT EXISTS extracted_text TEXT
        """,
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS account_manager TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS deal_id TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS deal_name TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pic_name TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pic_contact TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pic_designation TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_information TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS request_type TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS required_completion_date DATE",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS requirement_details TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS winning_probability INTEGER",
        """
        CREATE INDEX IF NOT EXISTS idx_projects_request_type
        ON projects (request_type)
        """,
        # Phase 2 Stage B — document intelligence
        "ALTER TABLE requirement_documents ADD COLUMN IF NOT EXISTS content_sha256 TEXT",
        "ALTER TABLE requirement_documents ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT",
        "ALTER TABLE requirement_documents ADD COLUMN IF NOT EXISTS mime_type TEXT",
        """
        ALTER TABLE requirement_documents
        ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'completed'
        """,
        "ALTER TABLE requirement_documents ADD COLUMN IF NOT EXISTS page_count INTEGER",
        "ALTER TABLE requirement_documents ADD COLUMN IF NOT EXISTS language TEXT",
        """
        ALTER TABLE requirement_documents
        ADD COLUMN IF NOT EXISTS ocr_used BOOLEAN NOT NULL DEFAULT FALSE
        """,
        """
        ALTER TABLE requirement_documents
        ADD COLUMN IF NOT EXISTS needs_manual_review BOOLEAN NOT NULL DEFAULT FALSE
        """,
        "ALTER TABLE requirement_documents ADD COLUMN IF NOT EXISTS error_message TEXT",
        "ALTER TABLE requirement_documents ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ",
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_documents_project_sha256
        ON requirement_documents (project_id, content_sha256)
        WHERE archived_at IS NULL
        """,
        """
        CREATE TABLE IF NOT EXISTS processing_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
            document_id UUID REFERENCES requirement_documents (id) ON DELETE SET NULL,
            job_type TEXT NOT NULL DEFAULT 'document_extract',
            status TEXT NOT NULL DEFAULT 'queued',
            progress INTEGER NOT NULL DEFAULT 0,
            error_message TEXT,
            result_json JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_processing_jobs_project_id
        ON processing_jobs (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_processing_jobs_document_id
        ON processing_jobs (document_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_processing_jobs_status
        ON processing_jobs (status)
        """,
        """
        CREATE TABLE IF NOT EXISTS document_pages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES requirement_documents (id) ON DELETE CASCADE,
            page_number INTEGER NOT NULL,
            text TEXT NOT NULL DEFAULT '',
            language TEXT,
            confidence DOUBLE PRECISION,
            char_count INTEGER NOT NULL DEFAULT 0,
            word_count INTEGER NOT NULL DEFAULT 0,
            ocr_engine TEXT,
            processing_ms INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (document_id, page_number)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_document_pages_document_id
        ON document_pages (document_id)
        """,
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES requirement_documents (id) ON DELETE CASCADE,
            page_number INTEGER,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            char_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (document_id, chunk_index)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
        ON document_chunks (document_id)
        """,
        """
        CREATE TABLE IF NOT EXISTS document_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES requirement_documents (id) ON DELETE CASCADE,
            key TEXT NOT NULL,
            value TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (document_id, key)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_document_metadata_document_id
        ON document_metadata (document_id)
        """,
        # Phase 2 Stage C — Draft RKM
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_models_project_id
        ON requirement_models (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_models_active_draft
        ON requirement_models (project_id)
        WHERE is_active_draft = TRUE
        """,
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirements_rkm_id ON requirements (rkm_id)
        """,
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_evidence_rkm_id
        ON requirement_evidence (rkm_id)
        """,
        """
        CREATE TABLE IF NOT EXISTS requirement_evidence_links (
            requirement_id UUID NOT NULL REFERENCES requirements (id) ON DELETE CASCADE,
            evidence_id UUID NOT NULL REFERENCES requirement_evidence (id) ON DELETE CASCADE,
            PRIMARY KEY (requirement_id, evidence_id)
        )
        """,
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
