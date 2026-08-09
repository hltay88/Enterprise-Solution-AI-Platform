-- Phase 3 Sprint 3.3 — Vendor catalogue, product mapping, BOM (ATLAS-032 / 035 / 038 / 039)
-- Global catalogue + project-scoped mapping/BOM. No solution_projects.
-- Architecture review/approve columns added on architecture_options for Complete gate.

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
);

CREATE INDEX IF NOT EXISTS idx_vendor_catalogues_created_at
ON vendor_catalogues (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vendor_catalogues_source
ON vendor_catalogues (source);

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
);

CREATE INDEX IF NOT EXISTS idx_vendor_products_catalogue_id
ON vendor_products (catalogue_id);

CREATE INDEX IF NOT EXISTS idx_vendor_products_vendor
ON vendor_products (vendor);

CREATE INDEX IF NOT EXISTS idx_vendor_products_category
ON vendor_products (category);

CREATE INDEX IF NOT EXISTS idx_vendor_products_lifecycle_status
ON vendor_products (lifecycle_status);

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
);

CREATE INDEX IF NOT EXISTS idx_product_capabilities_product_id
ON product_capabilities (product_id);

CREATE INDEX IF NOT EXISTS idx_product_capabilities_capability_code
ON product_capabilities (capability_code);

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
);

CREATE INDEX IF NOT EXISTS idx_architecture_product_mappings_project_id
ON architecture_product_mappings (project_id);

CREATE INDEX IF NOT EXISTS idx_architecture_product_mappings_architecture_id
ON architecture_product_mappings (architecture_id);

CREATE INDEX IF NOT EXISTS idx_architecture_product_mappings_component_id
ON architecture_product_mappings (component_id);

CREATE INDEX IF NOT EXISTS idx_architecture_product_mappings_product_id
ON architecture_product_mappings (product_id);

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
);

CREATE INDEX IF NOT EXISTS idx_bom_imports_project_id
ON bom_imports (project_id);

CREATE INDEX IF NOT EXISTS idx_bom_imports_architecture_id
ON bom_imports (architecture_id);

CREATE INDEX IF NOT EXISTS idx_bom_imports_created_at
ON bom_imports (created_at DESC);

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
);

CREATE INDEX IF NOT EXISTS idx_bom_items_bom_import_id
ON bom_items (bom_import_id);

CREATE INDEX IF NOT EXISTS idx_bom_items_mapped_product_id
ON bom_items (mapped_product_id);

CREATE TABLE IF NOT EXISTS bom_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bom_import_id UUID NOT NULL REFERENCES bom_imports (id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'needs_review',
    summary TEXT NOT NULL DEFAULT '',
    issues JSONB NOT NULL DEFAULT '[]'::jsonb,
    validated_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bom_validation_results_bom_import_id
ON bom_validation_results (bom_import_id);

CREATE INDEX IF NOT EXISTS idx_bom_validation_results_project_id
ON bom_validation_results (project_id);

-- Architecture review / approve pins (ATLAS-037).
ALTER TABLE architecture_options
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

ALTER TABLE architecture_options
    ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES users (id) ON DELETE SET NULL;

ALTER TABLE architecture_options
    ADD COLUMN IF NOT EXISTS review_note TEXT;

ALTER TABLE architecture_options
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;

ALTER TABLE architecture_options
    ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES users (id) ON DELETE SET NULL;

ALTER TABLE architecture_options
    ADD COLUMN IF NOT EXISTS approval_note TEXT;

-- Vendor/product stage on requirement traceability chain.
ALTER TABLE requirement_traceability
    ADD COLUMN IF NOT EXISTS product_id UUID;

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
END $$;

CREATE INDEX IF NOT EXISTS idx_requirement_traceability_product_id
ON requirement_traceability (product_id);
