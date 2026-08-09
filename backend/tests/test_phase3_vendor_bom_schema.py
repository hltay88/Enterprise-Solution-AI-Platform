"""Sprint 3.3 Task 1 — vendor catalogue / mapping / BOM schema freeze."""

from __future__ import annotations

from pathlib import Path

from app.models import (
    ArchitectureOption,
    ArchitectureProductMapping,
    BomImport,
    BomItem,
    BomValidationResult,
    ProductCapability,
    RequirementTraceability,
    VendorCatalogue,
    VendorProduct,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_SQL = REPO_ROOT / "docker" / "postgres" / "init" / "09_phase3_vendors_bom.sql"
SCHEMA_PY = REPO_ROOT / "backend" / "app" / "db" / "schema.py"

EXPECTED_TABLES = (
    "vendor_catalogues",
    "vendor_products",
    "product_capabilities",
    "architecture_product_mappings",
    "bom_imports",
    "bom_items",
    "bom_validation_results",
)


def test_init_sql_defines_sprint_3_3_tables():
    sql = INIT_SQL.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS solution_projects" not in sql
    assert "REFERENCES projects" in sql
    assert "REFERENCES architecture_options" in sql
    assert "REFERENCES architecture_components" in sql
    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
    assert "fk_requirement_traceability_product_id" in sql
    assert "ADD COLUMN IF NOT EXISTS reviewed_at" in sql
    assert "ADD COLUMN IF NOT EXISTS approved_at" in sql
    assert "is_stale" in sql
    assert "bom_validation_results" in sql


def test_ensure_schema_mirrors_vendor_bom_tables():
    source = SCHEMA_PY.read_text(encoding="utf-8")
    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in source
    assert "fk_requirement_traceability_product_id" in source
    assert "ADD COLUMN IF NOT EXISTS reviewed_at" in source
    assert "ADD COLUMN IF NOT EXISTS approved_by" in source


def test_orm_table_names():
    assert VendorCatalogue.__tablename__ == "vendor_catalogues"
    assert VendorProduct.__tablename__ == "vendor_products"
    assert ProductCapability.__tablename__ == "product_capabilities"
    assert ArchitectureProductMapping.__tablename__ == "architecture_product_mappings"
    assert BomImport.__tablename__ == "bom_imports"
    assert BomItem.__tablename__ == "bom_items"
    assert BomValidationResult.__tablename__ == "bom_validation_results"


def test_vendor_product_has_source_and_stale_flags():
    columns = set(VendorProduct.__table__.columns.keys())
    for name in (
        "catalogue_id",
        "vendor",
        "product_model",
        "category",
        "specifications",
        "lifecycle_status",
        "source",
        "source_date",
        "region",
        "confidence",
        "is_stale",
    ):
        assert name in columns


def test_bom_import_is_immutable_snapshot_shape():
    columns = set(BomImport.__table__.columns.keys())
    for name in (
        "project_id",
        "architecture_id",
        "source",
        "source_filename",
        "payload_json",
        "imported_by",
        "created_at",
    ):
        assert name in columns
    # Validation is a separate record (ATLAS-039).
    assert "status" not in columns


def test_architecture_option_has_review_approve_columns():
    columns = set(ArchitectureOption.__table__.columns.keys())
    for name in (
        "reviewed_at",
        "reviewed_by",
        "review_note",
        "approved_at",
        "approved_by",
        "approval_note",
    ):
        assert name in columns


def test_traceability_has_product_id():
    columns = set(RequirementTraceability.__table__.columns.keys())
    assert "product_id" in columns
