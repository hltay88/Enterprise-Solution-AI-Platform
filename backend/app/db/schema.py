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
        # Phase 2 Stage F — hardening
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'editor'
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
            user_id UUID REFERENCES users (id) ON DELETE SET NULL,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id UUID,
            summary TEXT NOT NULL DEFAULT '',
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_logs_project_id
        ON audit_logs (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
        ON audit_logs (created_at DESC)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action
        ON audit_logs (action)
        """,
        # Phase 3 — architecture recommendations
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_models_project_id
        ON architecture_models (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_models_created_at
        ON architecture_models (created_at DESC)
        """,
        # Phase 3 Sprint 3.1 — domain identification + requirement→domain traceability
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_domain_analyses_project_id
        ON domain_analyses (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_domain_analyses_created_at
        ON domain_analyses (created_at DESC)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_domain_analyses_rkm_id
        ON domain_analyses (rkm_id)
        """,
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_solution_domains_analysis_id
        ON solution_domains (analysis_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_solution_domains_project_id
        ON solution_domains (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_solution_domains_domain_code
        ON solution_domains (domain_code)
        """,
        """
        CREATE TABLE IF NOT EXISTS domain_requirement_links (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            domain_id UUID NOT NULL REFERENCES solution_domains (id) ON DELETE CASCADE,
            requirement_id TEXT NOT NULL,
            evidence TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_domain_requirement_links UNIQUE (domain_id, requirement_id)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_domain_requirement_links_domain_id
        ON domain_requirement_links (domain_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_domain_requirement_links_requirement_id
        ON domain_requirement_links (requirement_id)
        """,
        """
        CREATE TABLE IF NOT EXISTS domain_dependencies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            domain_id UUID NOT NULL REFERENCES solution_domains (id) ON DELETE CASCADE,
            depends_on_domain_code TEXT NOT NULL,
            dependency_kind TEXT NOT NULL DEFAULT 'required',
            reason TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_domain_dependencies_domain_id
        ON domain_dependencies (domain_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_domain_dependencies_depends_on
        ON domain_dependencies (depends_on_domain_code)
        """,
        """
        CREATE TABLE IF NOT EXISTS domain_open_questions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            analysis_id UUID NOT NULL REFERENCES domain_analyses (id) ON DELETE CASCADE,
            domain_id UUID REFERENCES solution_domains (id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            affects_selection BOOLEAN NOT NULL DEFAULT TRUE,
            related_requirement_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_domain_open_questions_analysis_id
        ON domain_open_questions (analysis_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_domain_open_questions_domain_id
        ON domain_open_questions (domain_id)
        """,
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_traceability_project_id
        ON requirement_traceability (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_traceability_analysis_id
        ON requirement_traceability (analysis_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_traceability_requirement_id
        ON requirement_traceability (requirement_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_traceability_domain_id
        ON requirement_traceability (domain_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_traceability_status
        ON requirement_traceability (status)
        """,
        # Phase 3 Sprint 3.2 — normalized architecture candidates
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_options_project_id
        ON architecture_options (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_options_generation_id
        ON architecture_options (generation_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_options_domain_analysis_id
        ON architecture_options (domain_analysis_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_options_created_at
        ON architecture_options (created_at DESC)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_options_status
        ON architecture_options (status)
        """,
        """
        CREATE TABLE IF NOT EXISTS architecture_components (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            purpose TEXT NOT NULL DEFAULT '',
            component_kind TEXT NOT NULL DEFAULT 'logical',
            sort_order INTEGER NOT NULL DEFAULT 0,
            maps_to_requirements JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_components_architecture_id
        ON architecture_components (architecture_id)
        """,
        """
        CREATE TABLE IF NOT EXISTS architecture_relationships (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
            from_component_id UUID NOT NULL REFERENCES architecture_components (id) ON DELETE CASCADE,
            to_component_id UUID NOT NULL REFERENCES architecture_components (id) ON DELETE CASCADE,
            relationship_kind TEXT NOT NULL DEFAULT 'connects_to',
            description TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_relationships_architecture_id
        ON architecture_relationships (architecture_id)
        """,
        """
        CREATE TABLE IF NOT EXISTS design_decisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
            decision TEXT NOT NULL,
            rationale TEXT NOT NULL DEFAULT '',
            impact TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_design_decisions_architecture_id
        ON design_decisions (architecture_id)
        """,
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_assumptions_architecture_id
        ON architecture_assumptions (architecture_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_assumptions_project_id
        ON architecture_assumptions (project_id)
        """,
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_solution_risks_architecture_id
        ON solution_risks (architecture_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_solution_risks_project_id
        ON solution_risks (project_id)
        """,
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_solution_scores_architecture_id
        ON solution_scores (architecture_id)
        """,
        """
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
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_capacity_notes_architecture_id
        ON capacity_notes (architecture_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_capacity_notes_project_id
        ON capacity_notes (project_id)
        """,
        """
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
        END $$
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_traceability_architecture_id
        ON requirement_traceability (architecture_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_traceability_component_id
        ON requirement_traceability (component_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_traceability_decision_id
        ON requirement_traceability (decision_id)
        """,
        # Phase 3 Sprint 3.3 — vendor catalogue, product mapping, BOM
        """
        CREATE TABLE IF NOT EXISTS vendor_catalogues (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT '',
            source_date DATE,
            version_label TEXT NOT NULL DEFAULT '1.0.0',
            region TEXT,
            notes TEXT,
            imported_by UUID REFERENCES users (id) ON DELETE SET NULL,
            payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_vendor_catalogues_created_at
        ON vendor_catalogues (created_at DESC)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_vendor_catalogues_source
        ON vendor_catalogues (source)
        """,
        """
        CREATE TABLE IF NOT EXISTS vendor_products (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            catalogue_id UUID NOT NULL REFERENCES vendor_catalogues (id) ON DELETE CASCADE,
            vendor TEXT NOT NULL,
            product_family TEXT NOT NULL DEFAULT '',
            product_model TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            specifications JSONB NOT NULL DEFAULT '{}'::jsonb,
            licensing TEXT,
            lifecycle_status TEXT NOT NULL DEFAULT 'unknown',
            source TEXT NOT NULL DEFAULT '',
            source_date DATE,
            region TEXT,
            confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
            is_stale BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_vendor_products_catalogue_vendor_model
                UNIQUE (catalogue_id, vendor, product_model)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_vendor_products_catalogue_id
        ON vendor_products (catalogue_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_vendor_products_vendor
        ON vendor_products (vendor)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_vendor_products_category
        ON vendor_products (category)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_vendor_products_lifecycle_status
        ON vendor_products (lifecycle_status)
        """,
        """
        CREATE TABLE IF NOT EXISTS product_capabilities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            product_id UUID NOT NULL REFERENCES vendor_products (id) ON DELETE CASCADE,
            capability_code TEXT NOT NULL,
            capability_label TEXT NOT NULL DEFAULT '',
            details JSONB NOT NULL DEFAULT '{}'::jsonb,
            confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_product_capabilities_product_code
                UNIQUE (product_id, capability_code)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_product_capabilities_product_id
        ON product_capabilities (product_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_product_capabilities_capability_code
        ON product_capabilities (capability_code)
        """,
        """
        CREATE TABLE IF NOT EXISTS architecture_product_mappings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
            architecture_id UUID NOT NULL REFERENCES architecture_options (id) ON DELETE CASCADE,
            component_id UUID NOT NULL REFERENCES architecture_components (id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES vendor_products (id) ON DELETE CASCADE,
            fit_score DOUBLE PRECISION,
            rationale TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'candidate',
            preference_kind TEXT NOT NULL DEFAULT 'technical',
            limitations TEXT NOT NULL DEFAULT '',
            created_by UUID REFERENCES users (id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_architecture_product_mappings_component_product
                UNIQUE (component_id, product_id)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_product_mappings_project_id
        ON architecture_product_mappings (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_product_mappings_architecture_id
        ON architecture_product_mappings (architecture_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_product_mappings_component_id
        ON architecture_product_mappings (component_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_architecture_product_mappings_product_id
        ON architecture_product_mappings (product_id)
        """,
        """
        CREATE TABLE IF NOT EXISTS bom_imports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
            architecture_id UUID REFERENCES architecture_options (id) ON DELETE SET NULL,
            source TEXT NOT NULL DEFAULT '',
            source_filename TEXT,
            notes TEXT,
            imported_by UUID REFERENCES users (id) ON DELETE SET NULL,
            payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_bom_imports_project_id
        ON bom_imports (project_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_bom_imports_architecture_id
        ON bom_imports (architecture_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_bom_imports_created_at
        ON bom_imports (created_at DESC)
        """,
        """
        CREATE TABLE IF NOT EXISTS bom_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            bom_import_id UUID NOT NULL REFERENCES bom_imports (id) ON DELETE CASCADE,
            line_number INTEGER NOT NULL DEFAULT 0,
            vendor TEXT NOT NULL DEFAULT '',
            product_model TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            quantity DOUBLE PRECISION,
            unit TEXT,
            category TEXT NOT NULL DEFAULT '',
            sku TEXT,
            mapped_product_id UUID REFERENCES vendor_products (id) ON DELETE SET NULL,
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_bom_items_bom_import_id
        ON bom_items (bom_import_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_bom_items_mapped_product_id
        ON bom_items (mapped_product_id)
        """,
        """
        CREATE TABLE IF NOT EXISTS bom_validation_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            bom_import_id UUID NOT NULL REFERENCES bom_imports (id) ON DELETE CASCADE,
            project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'needs_review',
            summary TEXT NOT NULL DEFAULT '',
            issues JSONB NOT NULL DEFAULT '[]'::jsonb,
            validated_by UUID REFERENCES users (id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_bom_validation_results_bom_import_id
        ON bom_validation_results (bom_import_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_bom_validation_results_project_id
        ON bom_validation_results (project_id)
        """,
        """
        ALTER TABLE architecture_options
            ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ
        """,
        """
        ALTER TABLE architecture_options
            ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES users (id) ON DELETE SET NULL
        """,
        """
        ALTER TABLE architecture_options
            ADD COLUMN IF NOT EXISTS review_note TEXT
        """,
        """
        ALTER TABLE architecture_options
            ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ
        """,
        """
        ALTER TABLE architecture_options
            ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES users (id) ON DELETE SET NULL
        """,
        """
        ALTER TABLE architecture_options
            ADD COLUMN IF NOT EXISTS approval_note TEXT
        """,
        """
        ALTER TABLE requirement_traceability
            ADD COLUMN IF NOT EXISTS product_id UUID
        """,
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_requirement_traceability_product_id'
            ) THEN
                ALTER TABLE requirement_traceability
                    ADD CONSTRAINT fk_requirement_traceability_product_id
                    FOREIGN KEY (product_id)
                    REFERENCES vendor_products (id)
                    ON DELETE SET NULL;
            END IF;
        END $$
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_requirement_traceability_product_id
        ON requirement_traceability (product_id)
        """,
        """
CREATE TABLE IF NOT EXISTS document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_templates_type_code UNIQUE (document_type, code)
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_document_templates_document_type
ON document_templates (document_type)
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_template_versions_template_id
ON template_versions (template_id)
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_source_snapshots_project_id
ON source_snapshots (project_id)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_source_snapshots_architecture_id
ON source_snapshots (architecture_id)
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_generation_runs_project_id
ON generation_runs (project_id)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_generation_runs_snapshot_id
ON generation_runs (source_snapshot_id)
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_generated_documents_project_id
ON generated_documents (project_id)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_generated_documents_project_type
ON generated_documents (project_id, document_type)
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_document_versions_document_id
ON document_versions (document_id)
        """,
        """
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
            ON DELETE SET NULL
        """,
        """
END IF
        """,
        """
END $$
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_document_sections_version_id
ON document_sections (document_version_id)
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_content_items_section_id
ON content_items (section_id)
        """,
        """
CREATE TABLE IF NOT EXISTS document_source_refs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_item_id UUID NOT NULL REFERENCES content_items (id) ON DELETE CASCADE,
    ref_kind TEXT NOT NULL,
    ref_id TEXT,
    label TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_document_source_refs_content_item_id
ON document_source_refs (content_item_id)
        """,
        """
CREATE TABLE IF NOT EXISTS document_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES document_versions (id) ON DELETE CASCADE,
    approver_id UUID REFERENCES users (id) ON DELETE SET NULL,
    decision TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_document_approvals_version_id
ON document_approvals (document_version_id)
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_export_jobs_project_id
ON export_jobs (project_id)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_export_jobs_document_id
ON export_jobs (document_id)
        """,
        """
INSERT INTO document_templates (id, document_type, code, name, active)
SELECT gen_random_uuid(), 'proposal', 'default_proposal', 'Default Proposal', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM document_templates
    WHERE document_type = 'proposal' AND code = 'default_proposal'
)
        """,
        """
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
  )
        """

        """
INSERT INTO document_templates (id, document_type, code, name, active)
SELECT gen_random_uuid(), 'presentation', 'default_presentation', 'Default Presentation', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM document_templates
    WHERE document_type = 'presentation' AND code = 'default_presentation'
)
        """,
        """
INSERT INTO template_versions (
    template_id, version_label, version_major, version_minor, version_patch,
    sections_json, styles_json, rendering_rules_json, status
)
SELECT
    t.id,
    '1.0.0', 1, 0, 0,
    '[{\"section_type\":\"title\",\"title\":\"Title\"},{\"section_type\":\"executive_summary\",\"title\":\"Executive Summary\"},{\"section_type\":\"customer_situation\",\"title\":\"Customer Situation\"},{\"section_type\":\"challenges\",\"title\":\"Challenges\"},{\"section_type\":\"requirements\",\"title\":\"Requirements\"},{\"section_type\":\"proposed_architecture\",\"title\":\"Proposed Architecture\"},{\"section_type\":\"solution_overview\",\"title\":\"Solution Overview\"},{\"section_type\":\"key_components\",\"title\":\"Key Components\"},{\"section_type\":\"technical_highlights\",\"title\":\"Technical Highlights\"},{\"section_type\":\"benefits\",\"title\":\"Benefits\"},{\"section_type\":\"implementation\",\"title\":\"Implementation\"},{\"section_type\":\"timeline\",\"title\":\"Timeline\"},{\"section_type\":\"risks_assumptions\",\"title\":\"Risks / Assumptions\"},{\"section_type\":\"next_steps\",\"title\":\"Next Steps\"}]'::jsonb,
    '{\"format\":\"pptx\"}'::jsonb,
    '{\"include_draft_watermark\": true}'::jsonb,
    'active'
FROM document_templates t
WHERE t.document_type = 'presentation' AND t.code = 'default_presentation'
  AND NOT EXISTS (
      SELECT 1 FROM template_versions tv
      WHERE tv.template_id = t.id
        AND tv.version_major = 1 AND tv.version_minor = 0 AND tv.version_patch = 0
  )
        """,
        """
INSERT INTO document_templates (id, document_type, code, name, active)
SELECT gen_random_uuid(), 'sow', 'default_sow', 'Default SOW', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM document_templates
    WHERE document_type = 'sow' AND code = 'default_sow'
)
        """,
        """
INSERT INTO template_versions (
    template_id, version_label, version_major, version_minor, version_patch,
    sections_json, styles_json, rendering_rules_json, status
)
SELECT
    t.id,
    '1.0.0', 1, 0, 0,
    '[{\"section_type\":\"purpose\",\"title\":\"Purpose\"},{\"section_type\":\"scope\",\"title\":\"Scope\"},{\"section_type\":\"solution_overview\",\"title\":\"Solution Overview\"},{\"section_type\":\"deliverables\",\"title\":\"Deliverables\"},{\"section_type\":\"implementation_activities\",\"title\":\"Implementation Activities\"},{\"section_type\":\"testing\",\"title\":\"Testing\"},{\"section_type\":\"acceptance_criteria\",\"title\":\"Acceptance Criteria\"},{\"section_type\":\"customer_responsibilities\",\"title\":\"Customer Responsibilities\"},{\"section_type\":\"provider_responsibilities\",\"title\":\"Provider Responsibilities\"},{\"section_type\":\"assumptions\",\"title\":\"Assumptions\"},{\"section_type\":\"exclusions\",\"title\":\"Exclusions\"},{\"section_type\":\"schedule\",\"title\":\"Schedule\"},{\"section_type\":\"support_warranty\",\"title\":\"Support / Warranty\"},{\"section_type\":\"change_control\",\"title\":\"Change Control\"}]'::jsonb,
    '{\"format\":\"docx\"}'::jsonb,
    '{\"include_draft_watermark\": true}'::jsonb,
    'active'
FROM document_templates t
WHERE t.document_type = 'sow' AND t.code = 'default_sow'
  AND NOT EXISTS (
      SELECT 1 FROM template_versions tv
      WHERE tv.template_id = t.id
        AND tv.version_major = 1 AND tv.version_minor = 0 AND tv.version_patch = 0
  )
        """,
        """
INSERT INTO document_templates (id, document_type, code, name, active)
SELECT gen_random_uuid(), 'solution_design', 'default_solution_design', 'Default Solution Design', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM document_templates
    WHERE document_type = 'solution_design' AND code = 'default_solution_design'
)
        """,
        """
INSERT INTO template_versions (
    template_id, version_label, version_major, version_minor, version_patch,
    sections_json, styles_json, rendering_rules_json, status
)
SELECT
    t.id,
    '1.0.0', 1, 0, 0,
    '[{\"section_type\":\"design_objectives\",\"title\":\"Design Objectives\"},{\"section_type\":\"scope\",\"title\":\"Scope\"},{\"section_type\":\"requirements_traceability\",\"title\":\"Requirements Traceability\"},{\"section_type\":\"high_level_architecture\",\"title\":\"High-level Architecture\"},{\"section_type\":\"logical_design\",\"title\":\"Logical Design\"},{\"section_type\":\"physical_component_design\",\"title\":\"Physical / Component Design\"},{\"section_type\":\"capacity\",\"title\":\"Capacity\"},{\"section_type\":\"security\",\"title\":\"Security\"},{\"section_type\":\"availability\",\"title\":\"Availability\"},{\"section_type\":\"integration\",\"title\":\"Integration\"},{\"section_type\":\"operations\",\"title\":\"Operations\"},{\"section_type\":\"monitoring\",\"title\":\"Monitoring\"},{\"section_type\":\"assumptions\",\"title\":\"Assumptions\"},{\"section_type\":\"risks\",\"title\":\"Risks\"},{\"section_type\":\"design_decisions\",\"title\":\"Design Decisions\"},{\"section_type\":\"appendices\",\"title\":\"Appendices\"}]'::jsonb,
    '{\"format\":\"docx\"}'::jsonb,
    '{\"include_draft_watermark\": true}'::jsonb,
    'active'
FROM document_templates t
WHERE t.document_type = 'solution_design' AND t.code = 'default_solution_design'
  AND NOT EXISTS (
      SELECT 1 FROM template_versions tv
      WHERE tv.template_id = t.id
        AND tv.version_major = 1 AND tv.version_minor = 0 AND tv.version_patch = 0
  )
        """,
        """
INSERT INTO document_templates (id, document_type, code, name, active)
SELECT gen_random_uuid(), 'bom', 'default_bom', 'Default BOM Package Sheet', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM document_templates
    WHERE document_type = 'bom' AND code = 'default_bom'
)
        """,
        """
INSERT INTO template_versions (
    template_id, version_label, version_major, version_minor, version_patch,
    sections_json, styles_json, rendering_rules_json, status
)
SELECT
    t.id,
    '1.0.0', 1, 0, 0,
    '[{\"section_type\":\"cover\",\"title\":\"Cover\"},{\"section_type\":\"line_items\",\"title\":\"Line Items\"},{\"section_type\":\"classification\",\"title\":\"Classification\"},{\"section_type\":\"issues\",\"title\":\"Issues\"},{\"section_type\":\"sources\",\"title\":\"Sources\"}]'::jsonb,
    '{\"format\":\"xlsx\"}'::jsonb,
    '{\"include_draft_watermark\": true}'::jsonb,
    'active'
FROM document_templates t
WHERE t.document_type = 'bom' AND t.code = 'default_bom'
  AND NOT EXISTS (
      SELECT 1 FROM template_versions tv
      WHERE tv.template_id = t.id
        AND tv.version_major = 1 AND tv.version_minor = 0 AND tv.version_patch = 0
  )
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_document_packages_project_id
ON document_packages (project_id)
        """,
        """
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
)
        """,
        """
CREATE INDEX IF NOT EXISTS idx_document_package_members_package_id
ON document_package_members (package_id)
        """,
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
